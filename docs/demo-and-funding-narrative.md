# Demo And Funding Narrative

KubePilot is an agentic AI Kubernetes operations platform. It helps operators
move from question to evidence to incident update without jumping between
runbooks, dashboards, terminals, and Kubernetes APIs.

## One-sentence Pitch

KubePilot turns Kubernetes failure signals, runbooks, and operational workflows
into evidence-backed AI guidance for DevOps and SRE teams.

## Problem

Kubernetes troubleshooting is fragmented. Engineers must correlate deployment
status, pod readiness, events, logs, runbooks, dashboards, and incident updates
under pressure.

## Product Answer

KubePilot provides a local-first AI operations workspace that:

- answers runbook-backed questions with citations
- detects unhealthy workloads
- diagnoses failing deployments
- shows agent workflow steps
- generates incident-room summaries
- proposes approval-gated remediation plans
- exposes metrics, traces, audit events, and alert rules
- deploys through Docker Compose, Helm, and ArgoCD

## Demo Flow

1. Start the stack:

   ```bash
   docker compose up -d --build
   ```

2. Open:

   ```text
   http://127.0.0.1:3000
   ```

3. Show the Dashboard:

   - runtime status
   - unhealthy workloads
   - platform capability map

4. Ask Copilot:

   ```text
   Show unhealthy workloads
   ```

   Point out source cards, citations, and agent steps.

5. Run Diagnosis for:

   ```text
   namespace: payments
   deployment: checkout
   ```

   Show pods, events, logs, recommendations, command palette, and remediation
   plan.

6. Open Incident:

   - severity
   - probable cause
   - operator impact
   - copy-ready status update
   - evidence timeline
   - next actions
   - markdown export

7. Open Observability:

   - trace duration bars
   - audit events
   - route groups
   - agent activity after the request

8. Optional monitoring profile:

   ```bash
   docker compose --profile monitoring up -d --build
   ```

   Open Prometheus at `http://127.0.0.1:9090` and Grafana at
   `http://127.0.0.1:3001`.

## What Makes It Credible

- The agent has explicit workflow steps instead of opaque chatbot output.
- Kubernetes access is behind fixture, service, kubeconfig, and in-cluster
  boundaries.
- Remediation is approval-gated and command-based rather than blindly executed.
- RAG sources are visible in the UI and testable through retrieval evaluation.
- Deployment assets include Helm, GitOps, monitoring, alerts, and CI checks.
- The local fixture mode makes demos reliable while real-cluster mode is
  documented and supported.

## Investor-facing Next Milestones

- Hosted demo environment with real SSO.
- Approval workflow for safe write actions.
- Multi-cluster support.
- Slack or incident-tool integration.
- Production secret management and enterprise audit export.
- Pilot with real SRE/DevOps users and collect measurable time-to-diagnosis
  improvement.
