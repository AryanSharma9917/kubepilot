# KubePilot

An AI-powered Kubernetes and DevOps copilot with RAG, tool-calling, GitOps
workflows, and observability.

The project is being built in small, runnable slices. The first slice provides
the FastAPI service foundation that future agent, RAG, and Kubernetes tools
will connect to.

## Current functionality

- Service metadata at `GET /`
- Liveness probe at `GET /healthz`
- Readiness probe at `GET /readyz`
- Environment-based service configuration
- API contract tests

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
