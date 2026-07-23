<p align="center">
  <img src="web/kubepilot-icon.svg" alt="KubePilot logo" width="96" />
</p>

<h1 align="center">KubePilot</h1>

<p align="center">
  Agentic AI Kubernetes operations workspace for troubleshooting, runbook retrieval,
  deployment diagnosis, incident reporting, and observability.
</p>

<p align="center">
  <strong>FastAPI</strong> · <strong>RAG</strong> · <strong>LangGraph-ready agent</strong> ·
  <strong>Go Kubernetes tool</strong> · <strong>Docker</strong> · <strong>Helm</strong> ·
  <strong>Prometheus/Grafana</strong>
</p>

---

## What Is KubePilot?

KubePilot is an agentic AI operations copilot for Kubernetes. It is built to help
engineers ask operational questions, inspect Kubernetes signals, retrieve runbook
context, diagnose failing deployments, and generate incident-ready reports from
one local-first workspace.

The goal is not to hide infrastructure behind a chatbot. KubePilot keeps the
tool boundary explicit: it retrieves evidence, calls Kubernetes inspection tools,
shows diagnosis details, records audit and trace data, and returns answers that a
human operator can review.

## Why It Was Built

Modern DevOps and SRE work often means switching between dashboards, terminals,
logs, runbooks, API docs, and incident templates. KubePilot explores how an AI
agent can reduce that context switching while still preserving explainability.

It was built as a production-style portfolio project that brings together:

- AI-assisted infrastructure operations
- Retrieval-Augmented Generation over runbooks
- Kubernetes health and deployment diagnosis
- Incident report generation
- Metrics, tracing, and audit events
- Containerized local demos and Kubernetes deployment assets
- A dark web console for presenting the workflow end to end

## Built By

**Aryan Sharma**  
DevOps / SRE focused engineer building agentic AI tools for infrastructure
operations.

## Current Demo

Run the full local demo stack:

```bash
docker compose up -d --build
```

Open the web console:

```text
http://127.0.0.1:3000
```

The Compose demo starts:

- Static web console on port `3000`
- FastAPI backend on port `8000`
- Go Kubernetes tool service on port `8081`
- Fixture-mode unhealthy workloads for a reliable demo

Useful demo prompts:

```text
Show unhealthy workloads
Why is checkout failing?
Create an incident report for deployment checkout
How do I troubleshoot ImagePullBackOff?
```

Verify the UI and same-origin API proxy:

```bash
./scripts/web-smoke.sh
```

Run the scripted demo guide:

```bash
./scripts/demo.sh
```

Run a kind/local-cluster demo with intentionally failing workloads:

```bash
./scripts/kind-demo.sh
```

## What Works Now

- Dark web console with Copilot, Dashboard, Diagnosis, Incident, Observability,
  and Documentation views
- Chat endpoint with deterministic offline answer synthesis
- Streaming chat endpoint
- Runbook loading, markdown chunking, and keyword retrieval
- Optional vector and FAISS retrieval paths
- Structured citations in chat responses
- Retrieval evaluation CLI for JSONL benchmark cases
- LangGraph-compatible orchestration boundary
- Intent routing for runbook, cluster health, diagnosis, and incident workflows
- Fixture-mode and real-client Kubernetes boundaries
- Go `k8s-tool` service for Kubernetes inspection
- Cluster health endpoint
- Deployment diagnosis endpoint with pods, events, logs, and recommendations
- JSON and markdown incident report generation
- Metrics endpoint for Prometheus-style scraping
- Local trace spans endpoint
- Local audit events endpoint
- Request ID propagation through API, traces, and audit events
- Optional API key authentication
- Optional in-memory rate limiting
- Namespace and action allowlists for cluster APIs
- Dockerfile and Docker Compose local stack
- Helm chart for Kubernetes deployment
- GitOps/ArgoCD starter manifest
- Prometheus config and starter Grafana dashboard
- Local cluster smoke workflow
- API and contract tests

## Architecture

```text
Browser UI
   |
   | same-origin /api proxy
   v
FastAPI API
   |
   | chat, status, knowledge, cluster, traces, audit
   v
Agent Layer
   |
   | intent routing, retrieval, tool calls, answer synthesis
   +----> RAG Layer
   |        markdown runbooks, keyword/vector/FAISS-ready retrieval
   |
   +----> Kubernetes Tool Boundary
            fixture mode, service mode, kubeconfig/in-cluster modes
            |
            v
          Go k8s-tool service
```

## Repository Map

```text
agent/                  Agent, graph workflow, tools, LLM providers, incidents
rag/                    Runbook loading, chunking, indexing, retrieval, eval
services/api/           FastAPI app, routes, auth, metrics, audit, tracing
services/k8s-tool/      Go Kubernetes inspection service
web/                    Static KubePilot console and brand assets
docs/runbooks/          Local operational runbooks for RAG
demo/kubernetes/        Intentionally broken demo workloads
helm/kubepilot/         Kubernetes deployment chart
gitops/argocd/          ArgoCD application starter manifest
monitoring/             Prometheus config and Grafana dashboard
scripts/                Demo, smoke, and local cluster workflows
tests/                  API, agent, RAG, and tool tests
```

## API Highlights

```text
GET  /
GET  /healthz
GET  /readyz
GET  /metrics
GET  /api/v1/status
POST /api/v1/chat
POST /api/v1/chat/stream
POST /api/v1/knowledge/search
GET  /api/v1/cluster/health
GET  /api/v1/cluster/namespaces/{namespace}/deployments/{name}/diagnose
GET  /api/v1/cluster/namespaces/{namespace}/deployments/{name}/incident-report
GET  /api/v1/cluster/namespaces/{namespace}/deployments/{name}/incident-report.md
GET  /api/v1/traces
GET  /api/v1/audit/events
```

Example:

```bash
curl http://127.0.0.1:8000/api/v1/cluster/health
```

Diagnosis:

```bash
curl http://127.0.0.1:8000/api/v1/cluster/namespaces/payments/deployments/checkout/diagnose
```

Markdown incident report:

```bash
curl http://127.0.0.1:8000/api/v1/cluster/namespaces/payments/deployments/checkout/incident-report.md
```

## Local Development

Python 3.11 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn kubepilot_api.main:app --reload
```

Open the generated API docs:

```text
http://127.0.0.1:8000/docs
```

Run checks:

```bash
pytest
ruff check .
```

## Retrieval

Build a persisted runbook index:

```bash
kubepilot-index --output .kubepilot/index/runbooks.json
```

Run the API with that index:

```bash
KUBEPILOT_RAG_INDEX_PATH=.kubepilot/index/runbooks.json \
  uvicorn kubepilot_api.main:app --reload
```

Run retrieval evaluation:

```bash
kubepilot-evaluate-retrieval --cases tests/fixtures/retrieval-evaluation.jsonl
kubepilot-evaluate-retrieval --report-output /tmp/kubepilot-retrieval-report.md
```

Build a FAISS sidecar index when optional FAISS dependencies are installed:

```bash
kubepilot-index \
  --output .kubepilot/index/runbooks.json \
  --faiss-output .kubepilot/index/runbooks.faiss
```

## Kubernetes And Deployment

Deploy with Helm:

```bash
helm upgrade --install kubepilot ./helm/kubepilot \
  --namespace kubepilot \
  --create-namespace
```

Run a local cluster smoke test:

```bash
./scripts/local-cluster-smoke.sh
```

See [docs/local-cluster.md](docs/local-cluster.md) for real-cluster mode notes.

Prometheus scrape config:

```text
monitoring/prometheus.yml
```

Starter Grafana dashboard:

```text
monitoring/grafana-dashboard.json
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `KUBEPILOT_APP_NAME` | `KubePilot API` | Display name |
| `KUBEPILOT_ENVIRONMENT` | `development` | Runtime environment |
| `KUBEPILOT_VERSION` | `0.1.0` | Reported service version |
| `KUBEPILOT_K8S_MODE` | `fixture` | Kubernetes mode: `fixture`, `kubeconfig`, or `in_cluster` |
| `KUBEPILOT_K8S_TOOL_MODE` | `fixture` | Go `k8s-tool` mode: `fixture` or `cluster` |
| `KUBEPILOT_K8S_SERVICE_URL` | `http://k8s-tool:8081` | Go Kubernetes tool service URL in service mode |
| `KUBEPILOT_KUBECONFIG` | unset | Optional kubeconfig path |
| `KUBEPILOT_ALLOWED_NAMESPACES` | unset | Optional namespace allowlist |
| `KUBEPILOT_ALLOWED_ACTIONS` | unset | Optional cluster action allowlist |
| `KUBEPILOT_API_KEYS` | unset | Optional comma-separated API keys for `/api/*` |
| `KUBEPILOT_RATE_LIMIT_PER_MINUTE` | `0` | Per-client API rate limit; `0` disables it |
| `KUBEPILOT_RAG_MODE` | `keyword` | Retrieval mode: `keyword`, `vector`, or `faiss` |
| `KUBEPILOT_RAG_INDEX_PATH` | unset | Optional persisted runbook index |
| `KUBEPILOT_LLM_PROVIDER` | `deterministic` | Answer provider mode |
| `KUBEPILOT_LLM_ENDPOINT` | unset | HTTP JSON LLM endpoint when provider is `http` |
| `KUBEPILOT_AGENT_MODE` | `deterministic` | Agent mode: `deterministic` or `langgraph` |
| `KUBEPILOT_OTEL_EXPORTER_OTLP_ENDPOINT` | unset | Optional OTLP HTTP trace export endpoint |
| `KUBEPILOT_OTEL_SERVICE_NAME` | `kubepilot-api` | OpenTelemetry service name |
| `KUBEPILOT_OTEL_HEADERS` | unset | Optional comma-separated `key=value` OTLP headers |

Optional dependency groups:

```bash
python -m pip install -e ".[kubernetes]"
python -m pip install -e ".[rag]"
python -m pip install -e ".[agent]"
python -m pip install -e ".[observability]"
```

## Roadmap

KubePilot is being built in runnable slices. The current foundation is in place;
future work can keep extending the same README sections as features land.

- Improve the web console visual polish and demo storytelling
- Expand real Kubernetes diagnosis coverage
- Add richer RAG evaluation cases and runbooks
- Wire FAISS retrieval as the default advanced retrieval path
- Deepen LangGraph orchestration flows
- Add stronger incident timeline views
- Expand Helm values and production deployment examples
- Improve GitOps and ArgoCD environment manifests
- Add richer monitoring dashboards and OpenTelemetry traces

See [ARCHITECTURE_AND_ROADMAP.md](ARCHITECTURE_AND_ROADMAP.md) for the detailed
architecture and implementation plan.
