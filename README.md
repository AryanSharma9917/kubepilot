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
- Initial agent boundary for chat-style requests
- Local markdown runbook loading, chunking, and keyword retrieval
- In-memory Kubernetes workload health inspector
- Environment-based service configuration
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

It can also be reached through chat prompts such as:

```text
Show unhealthy workloads
```

The agent detects the cluster-health intent, calls the inspector, and includes
unhealthy workload details in the response.

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

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `KUBEPILOT_APP_NAME` | `KubePilot API` | Display name |
| `KUBEPILOT_ENVIRONMENT` | `development` | Runtime environment |
| `KUBEPILOT_VERSION` | `0.1.0` | Reported service version |

See [ARCHITECTURE_AND_ROADMAP.md](ARCHITECTURE_AND_ROADMAP.md) for the target
architecture and MVP definition.
