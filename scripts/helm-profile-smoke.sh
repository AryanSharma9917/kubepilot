#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHART_DIR="${ROOT_DIR}/helm/kubepilot"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_command helm

profiles=("default" "local" "staging" "production")
for profile in "${profiles[@]}"; do
  if [[ "$profile" == "default" ]]; then
    helm template kubepilot "${CHART_DIR}" --namespace kubepilot >/tmp/kubepilot-${profile}.yaml
  else
    helm template kubepilot "${CHART_DIR}" \
      --namespace kubepilot \
      --values "${CHART_DIR}/values-${profile}.yaml" \
      >/tmp/kubepilot-${profile}.yaml
  fi
  echo "Rendered Helm profile: ${profile}"
done

echo "All Helm profiles rendered successfully."
