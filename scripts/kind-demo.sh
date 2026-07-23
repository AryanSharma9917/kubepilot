#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${KUBEPILOT_NAMESPACE:-kubepilot}"
RELEASE="${KUBEPILOT_RELEASE:-kubepilot}"
IMAGE="${KUBEPILOT_IMAGE:-kubepilot-api:demo}"
CLUSTER="${KUBEPILOT_KIND_CLUSTER:-kind}"
LOCAL_PORT="${KUBEPILOT_DEMO_PORT:-18000}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_command docker
require_command helm
require_command kubectl
require_command kind

if ! kind get clusters | grep -qx "${CLUSTER}"; then
  kind create cluster --name "${CLUSTER}"
fi

docker build -t "${IMAGE}" .
kind load docker-image "${IMAGE}" --name "${CLUSTER}"

kubectl apply -f demo/kubernetes/namespace.yaml
kubectl apply -f demo/kubernetes/checkout-broken.yaml
kubectl apply -f demo/kubernetes/metrics-scraper-broken.yaml

helm upgrade --install "${RELEASE}" ./helm/kubepilot \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  --set image.repository="${IMAGE%:*}" \
  --set image.tag="${IMAGE##*:}" \
  --set image.pullPolicy=IfNotPresent \
  --set env.KUBEPILOT_K8S_MODE=in_cluster

kubectl rollout status "deployment/${RELEASE}-kubepilot" \
  --namespace "${NAMESPACE}" \
  --timeout=120s

echo "KubePilot is deployed in kind with demo workloads."
echo "Run this to open the API locally:"
echo "kubectl port-forward service/${RELEASE}-kubepilot ${LOCAL_PORT}:8000 --namespace ${NAMESPACE}"
echo
echo "Then inspect:"
echo "http://127.0.0.1:${LOCAL_PORT}/api/v1/cluster/health"
