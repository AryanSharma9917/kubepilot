#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${KUBEPILOT_NAMESPACE:-kubepilot}"
RELEASE="${KUBEPILOT_RELEASE:-kubepilot}"
IMAGE="${KUBEPILOT_IMAGE:-kubepilot-api:local}"
CLUSTER="${KUBEPILOT_KIND_CLUSTER:-kind}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_command docker
require_command helm
require_command kubectl
require_command python

docker build -t "${IMAGE}" .

if command -v kind >/dev/null 2>&1; then
  kind load docker-image "${IMAGE}" --name "${CLUSTER}"
fi

helm template "${RELEASE}" ./helm/kubepilot \
  --namespace "${NAMESPACE}" \
  --set image.repository="${IMAGE%:*}" \
  --set image.tag="${IMAGE##*:}" \
  >/tmp/kubepilot-rendered.yaml

helm upgrade --install "${RELEASE}" ./helm/kubepilot \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  --set image.repository="${IMAGE%:*}" \
  --set image.tag="${IMAGE##*:}" \
  --set image.pullPolicy=IfNotPresent

kubectl rollout status "deployment/${RELEASE}-kubepilot" \
  --namespace "${NAMESPACE}" \
  --timeout=120s

kubectl port-forward "service/${RELEASE}-kubepilot" 18000:8000 \
  --namespace "${NAMESPACE}" >/tmp/kubepilot-port-forward.log 2>&1 &
PORT_FORWARD_PID="$!"
trap 'kill "${PORT_FORWARD_PID}" >/dev/null 2>&1 || true' EXIT

PYTHONPATH="services/api${PYTHONPATH:+:${PYTHONPATH}}" python -m kubepilot_api.local_cluster \
  --base-url http://127.0.0.1:18000 \
  --timeout 120 \
  --poll-interval 1

echo "KubePilot local cluster smoke test passed."
