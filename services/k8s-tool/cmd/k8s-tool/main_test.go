package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
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

func serveRequest(method string, path string) *httptest.ResponseRecorder {
	request := httptest.NewRequest(method, path, nil)
	response := httptest.NewRecorder()
	newRouter().ServeHTTP(response, request)
	return response
}
