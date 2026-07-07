package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strings"
)

type workloadHealth struct {
	Namespace       string `json:"namespace"`
	Name            string `json:"name"`
	Kind            string `json:"kind"`
	DesiredReplicas int    `json:"desired_replicas"`
	ReadyReplicas   int    `json:"ready_replicas"`
	Status          string `json:"status"`
	Reason          string `json:"reason"`
}

type podStatus struct {
	Namespace    string  `json:"namespace"`
	Name         string  `json:"name"`
	Phase        string  `json:"phase"`
	Ready        bool    `json:"ready"`
	RestartCount int     `json:"restart_count"`
	Reason       *string `json:"reason,omitempty"`
}

type kubernetesEvent struct {
	Namespace      string `json:"namespace"`
	InvolvedObject string `json:"involved_object"`
	Reason         string `json:"reason"`
	Message        string `json:"message"`
	EventType      string `json:"event_type"`
}

type containerLog struct {
	Namespace     string `json:"namespace"`
	PodName       string `json:"pod_name"`
	ContainerName string `json:"container_name"`
	Text          string `json:"text"`
	Previous      bool   `json:"previous"`
}

type clusterHealthResponse struct {
	Workloads []workloadHealth `json:"workloads"`
}

type deploymentDiagnosisResponse struct {
	Namespace       string            `json:"namespace"`
	Name            string            `json:"name"`
	Health          workloadHealth    `json:"health"`
	Pods            []podStatus       `json:"pods"`
	Events          []kubernetesEvent `json:"events"`
	Logs            []containerLog    `json:"logs"`
	Recommendations []string          `json:"recommendations"`
}

func main() {
	addr := os.Getenv("KUBEPILOT_K8S_TOOL_ADDR")
	if addr == "" {
		addr = ":8081"
	}

	log.Printf("starting kubepilot k8s-tool on %s", addr)
	if err := http.ListenAndServe(addr, newRouter()); err != nil {
		log.Fatal(err)
	}
}

func newRouter() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", healthz)
	mux.HandleFunc("/api/v1/cluster/health", clusterHealth)
	mux.HandleFunc("/api/v1/namespaces/", deploymentDiagnosis)
	return mux
}

func healthz(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func clusterHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	namespace := r.URL.Query().Get("namespace")
	workloads := fixtureWorkloads()
	if namespace != "" {
		filtered := make([]workloadHealth, 0)
		for _, workload := range workloads {
			if workload.Namespace == namespace {
				filtered = append(filtered, workload)
			}
		}
		workloads = filtered
	}

	writeJSON(w, http.StatusOK, clusterHealthResponse{Workloads: workloads})
}

func deploymentDiagnosis(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	namespace, name, ok := parseDeploymentPath(r.URL.Path)
	if !ok {
		http.NotFound(w, r)
		return
	}

	diagnosis, found := fixtureDiagnosis(namespace, name)
	if !found {
		http.NotFound(w, r)
		return
	}

	writeJSON(w, http.StatusOK, diagnosis)
}

func parseDeploymentPath(path string) (string, string, bool) {
	parts := strings.Split(strings.Trim(path, "/"), "/")
	if len(parts) != 6 {
		return "", "", false
	}
	if parts[0] != "api" || parts[1] != "v1" || parts[2] != "namespaces" {
		return "", "", false
	}
	if parts[4] != "deployments" || parts[5] == "" || parts[3] == "" {
		return "", "", false
	}
	return parts[3], parts[5], true
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(payload); err != nil {
		log.Printf("failed to encode response: %v", err)
	}
}

func fixtureWorkloads() []workloadHealth {
	return []workloadHealth{
		{
			Namespace:       "default",
			Name:            "kubepilot-api",
			Kind:            "Deployment",
			DesiredReplicas: 2,
			ReadyReplicas:   2,
			Status:          "Healthy",
			Reason:          "All replicas are ready",
		},
		{
			Namespace:       "payments",
			Name:            "checkout",
			Kind:            "Deployment",
			DesiredReplicas: 3,
			ReadyReplicas:   1,
			Status:          "Degraded",
			Reason:          "Two replicas are unavailable",
		},
		{
			Namespace:       "platform",
			Name:            "metrics-scraper",
			Kind:            "Deployment",
			DesiredReplicas: 1,
			ReadyReplicas:   0,
			Status:          "Degraded",
			Reason:          "Readiness probe is failing",
		},
	}
}

func fixtureDiagnosis(namespace string, name string) (deploymentDiagnosisResponse, bool) {
	if namespace != "payments" || name != "checkout" {
		return deploymentDiagnosisResponse{}, false
	}

	crashLoop := "CrashLoopBackOff"
	imagePull := "ImagePullBackOff"
	return deploymentDiagnosisResponse{
		Namespace: namespace,
		Name:      name,
		Health: workloadHealth{
			Namespace:       namespace,
			Name:            name,
			Kind:            "Deployment",
			DesiredReplicas: 3,
			ReadyReplicas:   1,
			Status:          "Degraded",
			Reason:          "Two replicas are unavailable",
		},
		Pods: []podStatus{
			{
				Namespace:    namespace,
				Name:         "checkout-7d8f5b9c6c-abc12",
				Phase:        "Running",
				Ready:        false,
				RestartCount: 5,
				Reason:       &crashLoop,
			},
			{
				Namespace:    namespace,
				Name:         "checkout-7d8f5b9c6c-def34",
				Phase:        "Pending",
				Ready:        false,
				RestartCount: 0,
				Reason:       &imagePull,
			},
		},
		Events: []kubernetesEvent{
			{
				Namespace:      namespace,
				InvolvedObject: "checkout-7d8f5b9c6c-def34",
				Reason:         "Failed",
				Message:        "Failed to pull image registry.example.com/checkout:bad-tag",
				EventType:      "Warning",
			},
		},
		Logs: []containerLog{
			{
				Namespace:     namespace,
				PodName:       "checkout-7d8f5b9c6c-abc12",
				ContainerName: "checkout",
				Text:          "panic: missing PAYMENT_GATEWAY_URL environment variable",
				Previous:      true,
			},
		},
		Recommendations: []string{
			"Verify the image name, tag, registry credentials, and pull secret.",
			"Inspect previous container logs and recent configuration changes.",
		},
	}, true
}
