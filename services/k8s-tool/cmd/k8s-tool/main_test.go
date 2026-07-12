package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

func TestHealthz(t *testing.T) {
	response := serveRequest(http.MethodGet, "/healthz")

	if response.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", response.Code)
	}
}

func TestClusterHealthFiltersByNamespace(t *testing.T) {
	response := serveRequest(http.MethodGet, "/api/v1/cluster/health?namespace=payments")

	var payload clusterHealthResponse
	if err := json.NewDecoder(response.Body).Decode(&payload); err != nil {
		t.Fatalf("decode cluster health: %v", err)
	}

	if len(payload.Workloads) != 1 {
		t.Fatalf("expected 1 workload, got %d", len(payload.Workloads))
	}
	if payload.Workloads[0].Name != "checkout" {
		t.Fatalf("expected checkout workload, got %s", payload.Workloads[0].Name)
	}
}

func TestDeploymentDiagnosis(t *testing.T) {
	response := serveRequest(http.MethodGet, "/api/v1/namespaces/payments/deployments/checkout")

	var payload deploymentDiagnosisResponse
	if err := json.NewDecoder(response.Body).Decode(&payload); err != nil {
		t.Fatalf("decode deployment diagnosis: %v", err)
	}

	if payload.Name != "checkout" {
		t.Fatalf("expected checkout diagnosis, got %s", payload.Name)
	}
	if len(payload.Pods) != 2 {
		t.Fatalf("expected 2 pods, got %d", len(payload.Pods))
	}
	if len(payload.Logs) != 1 || !payload.Logs[0].Previous {
		t.Fatalf("expected previous log evidence, got %#v", payload.Logs)
	}
}

func TestDeploymentDiagnosisNotFound(t *testing.T) {
	response := serveRequest(http.MethodGet, "/api/v1/namespaces/default/deployments/missing")

	if response.Code != http.StatusNotFound {
		t.Fatalf("expected 404, got %d", response.Code)
	}
}

func TestDeploymentHealthMapsUnavailableReplicas(t *testing.T) {
	desired := int32(3)
	health := deploymentHealth(appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Namespace: "payments",
			Name:      "checkout",
		},
		Spec: appsv1.DeploymentSpec{Replicas: &desired},
		Status: appsv1.DeploymentStatus{
			ReadyReplicas: 1,
		},
	})

	if health.Status != "Degraded" {
		t.Fatalf("expected degraded deployment, got %s", health.Status)
	}
	if health.DesiredReplicas != 3 || health.ReadyReplicas != 1 {
		t.Fatalf("unexpected replica summary: %#v", health)
	}
}

func TestPodStatusListCapturesWaitingReason(t *testing.T) {
	pods := podStatusList([]corev1.Pod{
		{
			ObjectMeta: metav1.ObjectMeta{
				Namespace: "payments",
				Name:      "checkout-abc",
			},
			Status: corev1.PodStatus{
				Phase: corev1.PodRunning,
				ContainerStatuses: []corev1.ContainerStatus{
					{
						Ready:        false,
						RestartCount: 3,
						State: corev1.ContainerState{
							Waiting: &corev1.ContainerStateWaiting{Reason: "CrashLoopBackOff"},
						},
					},
				},
			},
		},
	})

	if len(pods) != 1 {
		t.Fatalf("expected 1 pod status, got %d", len(pods))
	}
	if pods[0].Reason == nil || *pods[0].Reason != "CrashLoopBackOff" {
		t.Fatalf("expected CrashLoopBackOff reason, got %#v", pods[0].Reason)
	}
}

func serveRequest(method string, path string) *httptest.ResponseRecorder {
	request := httptest.NewRequest(method, path, nil)
	response := httptest.NewRecorder()
	newRouter(fixtureInspector{}).ServeHTTP(response, request)
	return response
}
