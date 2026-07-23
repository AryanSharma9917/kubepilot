#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${KUBEPILOT_WEB_URL:-http://127.0.0.1:3000}"

require_path() {
  local path="$1"
  local expected="$2"
  local body
  body="$(curl -fsS "${BASE_URL}${path}")"
  if ! grep -q "${expected}" <<<"${body}"; then
    echo "Expected ${BASE_URL}${path} to contain: ${expected}" >&2
    exit 1
  fi
}

require_path "/" "KubePilot"
require_path "/api/v1/status" "\"environment\""
require_path "/api/v1/cluster/health" "\"unhealthy_count\""

echo "KubePilot web smoke test passed for ${BASE_URL}"
