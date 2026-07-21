#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
KubePilot demo

1. Start the stack:
   docker compose up --build

2. Open the UI:
   http://127.0.0.1:3000

3. Try the copilot prompt:
   Create an incident report for deployment checkout

4. Inspect direct API docs:
   http://127.0.0.1:8000/docs

5. Useful demo endpoints:
   http://127.0.0.1:8000/api/v1/status
   http://127.0.0.1:8000/api/v1/cluster/health
   http://127.0.0.1:8000/api/v1/cluster/namespaces/payments/deployments/checkout/diagnose
   http://127.0.0.1:8000/api/v1/cluster/namespaces/payments/deployments/checkout/incident-report.md
EOF
