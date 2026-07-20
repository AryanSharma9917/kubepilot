package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strings"
	"time"
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

type kubernetesInspector interface {
	ClusterHealth(ctx context.Context, namespace string) ([]workloadHealth, error)
	DeploymentDiagnosis(ctx context.Context, namespace string, name string) (deploymentDiagnosisResponse, bool, error)
}

func main() {
	if len(os.Args) > 1 && os.Args[1] == "healthcheck" {
		if err := runHealthcheck(); err != nil {
			log.Fatal(err)
		}
		return
	}

	addr := os.Getenv("KUBEPILOT_K8S_TOOL_ADDR")
	if addr == "" {
		addr = ":8081"
	}

	log.Printf("starting kubepilot k8s-tool on %s", addr)
	if err := http.ListenAndServe(addr, newRouter(newInspectorFromEnv())); err != nil {
		log.Fatal(err)
	}
}

func runHealthcheck() error {
	url := os.Getenv("KUBEPILOT_K8S_TOOL_HEALTHCHECK_URL")
	if url == "" {
		url = "http://127.0.0.1:8081/healthz"
	}
	client := http.Client{Timeout: 2 * time.Second}
	response, err := client.Get(url)
	if err != nil {
		return err
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK {
		return errUnexpectedStatus(response.StatusCode)
	}
	return nil
}

type errUnexpectedStatus int

func (err errUnexpectedStatus) Error() string {
	return "unexpected healthcheck status: " + http.StatusText(int(err))
}

func newRouter(inspector kubernetesInspector) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", healthz)
	mux.HandleFunc("/api/v1/cluster/health", clusterHealth(inspector))
	mux.HandleFunc("/api/v1/namespaces/", deploymentDiagnosis(inspector))
	return mux
}

func healthz(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func clusterHealth(inspector kubernetesInspector) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		namespace := r.URL.Query().Get("namespace")
		workloads, err := inspector.ClusterHealth(r.Context(), namespace)
		if err != nil {
			http.Error(w, "cluster inspection failed", http.StatusInternalServerError)
			return
		}

		writeJSON(w, http.StatusOK, clusterHealthResponse{Workloads: workloads})
	}
}

func deploymentDiagnosis(inspector kubernetesInspector) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		namespace, name, ok := parseDeploymentPath(r.URL.Path)
		if !ok {
			http.NotFound(w, r)
			return
		}

		diagnosis, found, err := inspector.DeploymentDiagnosis(r.Context(), namespace, name)
		if err != nil {
			http.Error(w, "deployment diagnosis failed", http.StatusInternalServerError)
			return
		}
		if !found {
			http.NotFound(w, r)
			return
		}

		writeJSON(w, http.StatusOK, diagnosis)
	}
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

func newInspectorFromEnv() kubernetesInspector {
	mode := os.Getenv("KUBEPILOT_K8S_TOOL_MODE")
	if mode == "" || mode == "fixture" {
		return fixtureInspector{}
	}
	if mode == "cluster" {
		inspector, err := newClusterInspector()
		if err != nil {
			log.Printf("falling back to fixture inspector: %v", err)
			return fixtureInspector{}
		}
		return inspector
	}
	log.Printf("unknown KUBEPILOT_K8S_TOOL_MODE=%q, using fixture inspector", mode)
	return fixtureInspector{}
}

type fixtureInspector struct{}

func (fixtureInspector) ClusterHealth(ctx context.Context, namespace string) ([]workloadHealth, error) {
	workloads := fixtureWorkloads()
	if namespace == "" {
		return workloads, nil
	}
	filtered := make([]workloadHealth, 0)
	for _, workload := range workloads {
		if workload.Namespace == namespace {
			filtered = append(filtered, workload)
		}
	}
	return filtered, nil
}

func (fixtureInspector) DeploymentDiagnosis(
	ctx context.Context,
	namespace string,
	name string,
) (deploymentDiagnosisResponse, bool, error) {
	diagnosis, found := fixtureDiagnosis(namespace, name)
	return diagnosis, found, nil
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
