# KubePilot

An AI-powered Kubernetes and DevOps copilot with RAG, tool-calling, GitOps
workflows, and observability.

The project is being built in small, runnable slices. The current version
provides a FastAPI service, an initial agent boundary, local runbook retrieval,
and a deterministic Kubernetes health tool that future LangGraph, vector search,
and real cluster clients will replace or extend.

## Current functionality

- Service metadata at `GET /`
- Liveness probe at `GET /healthz`
- Readiness probe at `GET /readyz`
- Chat endpoint at `POST /api/v1/chat`
- Streaming chat endpoint at `POST /api/v1/chat/stream`
- Knowledge search endpoint at `POST /api/v1/knowledge/search`
- Cluster health endpoint at `GET /api/v1/cluster/health`
- Deployment diagnosis endpoint at
  `GET /api/v1/cluster/namespaces/{namespace}/deployments/{name}/diagnose`
- Deployment incident report endpoint at
  `GET /api/v1/cluster/namespaces/{namespace}/deployments/{name}/incident-report`
- Markdown incident report export at
  `GET /api/v1/cluster/namespaces/{namespace}/deployments/{name}/incident-report.md`
- Redacted runtime status endpoint at `GET /api/v1/status`
- Initial agent boundary for chat-style requests
- Local markdown runbook loading, chunking, and keyword retrieval
- Optional vector retrieval with FAISS when installed
- Provider-shaped answer synthesis with an offline deterministic LLM client
- Self-hosted HTTP JSON LLM provider support
- Structured answer citations in chat responses
- Retrieval evaluation CLI for JSONL benchmark cases
- LangGraph-compatible agent orchestration boundary
- Explicit graph workflow step plans for agent intents
- Branch-specific graph nodes for retrieval, tool execution, synthesis, and review
- Graph output review before returning responses
- Fixture-mode and real-client Kubernetes tool boundary
- Environment-based service configuration
- Prometheus-style metrics at `GET /metrics`
- Operation metrics for retrieval, cluster tools, chat, and trace buffering
- Local audit events at `GET /api/v1/audit/events`
- Local trace spans at `GET /api/v1/traces`
- Request ID propagation through `X-Request-ID` and audit events
- Optional API key authentication for `/api/*` routes
- Optional in-memory rate limiting for `/api/*` routes
- Namespace and action allowlists for cluster tool APIs
- Docker, Compose, Helm, Prometheus, Grafana, and GitOps starter manifests
- API contract tests

## Local knowledge flow

KubePilot currently retrieves context from markdown runbooks in
`docs/runbooks/`.

When a user sends a chat message:

1. FastAPI validates the request.
2. The chat service passes the message into the agent boundary.
3. The agent searches local runbook chunks with the keyword retriever.
4. The answer synthesizer builds a grounded prompt from retrieved context.
5. The configured LLM provider returns an answer.
6. The API returns the answer, source titles, and structured citations.

This keeps the project runnable without external AI or vector database
dependencies while preserving the architecture seam for hosted LLMs, FAISS,
sentence transformers, and LangGraph later.

## Local cluster tool flow

KubePilot also has a Kubernetes health inspector for local development. It
defaults to fixture workload health so the API and agent tool-calling path can
be tested without a live cluster, and can switch to kubeconfig, in-cluster, or
Go tool service modes for real cluster inspection.

Cluster health can be queried directly:

```bash
curl http://127.0.0.1:8000/api/v1/cluster/health
```

Deployment diagnosis can also be queried directly:

```bash
curl http://127.0.0.1:8000/api/v1/cluster/namespaces/payments/deployments/checkout/diagnose
```

KubePilot can also return a structured incident report:

```bash
curl http://127.0.0.1:8000/api/v1/cluster/namespaces/payments/deployments/checkout/incident-report
```

Export the same report as markdown:

```bash
curl http://127.0.0.1:8000/api/v1/cluster/namespaces/payments/deployments/checkout/incident-report.md
```

It can also be reached through chat prompts such as:

```text
Show unhealthy workloads
Diagnose deployment checkout
Create an incident report for deployment checkout
```

The agent detects the cluster-health, diagnosis, or incident-report intent,
calls the relevant tool boundary, and includes workload details or next actions
in the response.

## Local development

Python 3.11 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn kubepilot_api.main:app --reload
```

Open <http://127.0.0.1:8000/docs> for the generated API documentation.

Run the checks with:

```bash
pytest
ruff check .
```

Build a persisted runbook index:

```bash
kubepilot-index --output .kubepilot/index/runbooks.json
KUBEPILOT_RAG_INDEX_PATH=.kubepilot/index/runbooks.json uvicorn kubepilot_api.main:app --reload
```

Run retrieval evaluation:

```bash
kubepilot-evaluate-retrieval --cases tests/fixtures/retrieval-evaluation.jsonl
kubepilot-evaluate-retrieval --report-output /tmp/kubepilot-retrieval-report.md
```

Build a native FAISS sidecar index when optional FAISS dependencies are
installed:

```bash
kubepilot-index \
  --output .kubepilot/index/runbooks.json \
  --faiss-output .kubepilot/index/runbooks.faiss
```

Run the API with Docker Compose:

```bash
docker compose up --build
```

Compose starts the web UI, FastAPI service, and Go `k8s-tool` service. Open
<http://127.0.0.1:3000> for the UI or <http://127.0.0.1:8000/docs> for the API
docs. The Go tool defaults to fixture mode locally; set
`KUBEPILOT_K8S_TOOL_MODE=cluster` for real cluster access when running it with
kubeconfig or in-cluster credentials.

Print the demo flow with:

```bash
./scripts/demo.sh
```

After the stack is running, verify the UI and same-origin API proxy with:

```bash
./scripts/web-smoke.sh
```

Deploy to a local Kubernetes cluster after building/loading the image:

```bash
helm upgrade --install kubepilot ./helm/kubepilot --namespace kubepilot --create-namespace
```

For an end-to-end local cluster smoke test, run:

```bash
./scripts/local-cluster-smoke.sh
```

See [docs/local-cluster.md](docs/local-cluster.md) for the manual workflow and
real-cluster mode notes. The local cluster smoke workflow can be run manually in
GitHub Actions and also runs on a weekly schedule.

Prometheus scrape configuration lives at
[monitoring/prometheus.yml](monitoring/prometheus.yml), and a starter Grafana
dashboard lives at
[monitoring/grafana-dashboard.json](monitoring/grafana-dashboard.json).
Set `KUBEPILOT_OTEL_EXPORTER_OTLP_ENDPOINT` to export OpenTelemetry traces to an
OTLP HTTP collector while keeping the local trace endpoint available.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `KUBEPILOT_APP_NAME` | `KubePilot API` | Display name |
| `KUBEPILOT_ENVIRONMENT` | `development` | Runtime environment |
| `KUBEPILOT_VERSION` | `0.1.0` | Reported service version |
| `KUBEPILOT_K8S_MODE` | `fixture` | Kubernetes mode: `fixture`, `kubeconfig`, or `in_cluster` |
| `KUBEPILOT_K8S_TOOL_MODE` | `fixture` | Go `k8s-tool` mode: `fixture` or `cluster` |
| `KUBEPILOT_K8S_SERVICE_URL` | `http://k8s-tool:8081` | Go Kubernetes tool service URL when using service mode |
| `KUBEPILOT_KUBECONFIG` | unset | Optional kubeconfig path for `kubeconfig` mode |
| `KUBEPILOT_ALLOWED_NAMESPACES` | unset | Optional comma-separated namespace allowlist for cluster APIs |
| `KUBEPILOT_ALLOWED_ACTIONS` | unset | Optional comma-separated action allowlist for cluster APIs |
| `KUBEPILOT_API_KEYS` | unset | Optional comma-separated API keys for `/api/*` routes |
| `KUBEPILOT_RATE_LIMIT_PER_MINUTE` | `0` | Optional per-client `/api/*` request limit; `0` disables it |
| `KUBEPILOT_RAG_MODE` | `keyword` | Retrieval mode: `keyword`, `vector`, or `faiss` |
| `KUBEPILOT_RAG_INDEX_PATH` | unset | Optional path to a persisted runbook index |
| `KUBEPILOT_LLM_PROVIDER` | `deterministic` | Answer provider mode; currently `deterministic` |
| `KUBEPILOT_LLM_ENDPOINT` | unset | HTTP JSON LLM endpoint when `KUBEPILOT_LLM_PROVIDER=http` |
| `KUBEPILOT_AGENT_MODE` | `deterministic` | Agent mode: `deterministic` or `langgraph` |
| `KUBEPILOT_OTEL_EXPORTER_OTLP_ENDPOINT` | unset | Optional OTLP HTTP trace export endpoint |
| `KUBEPILOT_OTEL_SERVICE_NAME` | `kubepilot-api` | OpenTelemetry service name |
| `KUBEPILOT_OTEL_HEADERS` | unset | Optional comma-separated `key=value` OTLP headers |

Optional integration dependencies are grouped as extras:

```bash
python -m pip install -e ".[kubernetes]"
python -m pip install -e ".[rag]"
python -m pip install -e ".[agent]"
python -m pip install -e ".[observability]"
```

See [ARCHITECTURE_AND_ROADMAP.md](ARCHITECTURE_AND_ROADMAP.md) for the target
architecture and MVP definition.
