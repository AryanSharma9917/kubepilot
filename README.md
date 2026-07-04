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
- Cluster health endpoint at `GET /api/v1/cluster/health`
- Deployment diagnosis endpoint at
  `GET /api/v1/cluster/namespaces/{namespace}/deployments/{name}/diagnose`
- Deployment incident report endpoint at
  `GET /api/v1/cluster/namespaces/{namespace}/deployments/{name}/incident-report`
- Initial agent boundary for chat-style requests
- Local markdown runbook loading, chunking, and keyword retrieval
- Optional vector retrieval with FAISS when installed
- LangGraph-compatible agent orchestration boundary
- Fixture-mode and real-client Kubernetes tool boundary
- Environment-based service configuration
- Prometheus-style metrics at `GET /metrics`
- Docker, Compose, Helm, monitoring, and GitOps starter manifests
- API contract tests

## Local knowledge flow

KubePilot currently retrieves context from markdown runbooks in
`docs/runbooks/`.

When a user sends a chat message:

1. FastAPI validates the request.
2. The chat service passes the message into the agent boundary.
3. The agent searches local runbook chunks with the keyword retriever.
4. The API returns a deterministic answer and matching runbook source titles.

This keeps the project runnable without external AI or vector database
dependencies while preserving the architecture seam for FAISS, sentence
transformers, and LangGraph later.

## Local cluster tool flow

KubePilot also has a deterministic Kubernetes health inspector for local
development. It does not connect to a real cluster yet; instead, it returns
fixture workload health so the API and agent tool-calling path can be tested.

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

Run the API with Docker Compose:

```bash
docker compose up --build
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
real-cluster mode notes.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `KUBEPILOT_APP_NAME` | `KubePilot API` | Display name |
| `KUBEPILOT_ENVIRONMENT` | `development` | Runtime environment |
| `KUBEPILOT_VERSION` | `0.1.0` | Reported service version |
| `KUBEPILOT_K8S_MODE` | `fixture` | Kubernetes mode: `fixture`, `kubeconfig`, or `in_cluster` |
| `KUBEPILOT_KUBECONFIG` | unset | Optional kubeconfig path for `kubeconfig` mode |
| `KUBEPILOT_RAG_MODE` | `keyword` | Retrieval mode: `keyword`, `vector`, or `faiss` |
| `KUBEPILOT_RAG_INDEX_PATH` | unset | Optional path to a persisted runbook index |
| `KUBEPILOT_AGENT_MODE` | `deterministic` | Agent mode: `deterministic` or `langgraph` |

Optional integration dependencies are grouped as extras:

```bash
python -m pip install -e ".[kubernetes]"
python -m pip install -e ".[rag]"
python -m pip install -e ".[agent]"
```

See [ARCHITECTURE_AND_ROADMAP.md](ARCHITECTURE_AND_ROADMAP.md) for the target
architecture and MVP definition.
