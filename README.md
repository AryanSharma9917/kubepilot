# KubePilot

An AI-powered Kubernetes and DevOps copilot with RAG, tool-calling, GitOps
workflows, and observability.

The project is being built in small, runnable slices. The current version
provides a FastAPI service, an initial agent boundary, and local runbook
retrieval that future LangGraph, vector search, and Kubernetes tools will
replace or extend.

## Current functionality

- Service metadata at `GET /`
- Liveness probe at `GET /healthz`
- Readiness probe at `GET /readyz`
- Chat endpoint at `POST /api/v1/chat`
- Initial agent boundary for chat-style requests
- Local markdown runbook loading, chunking, and keyword retrieval
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
