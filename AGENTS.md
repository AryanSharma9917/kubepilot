# AGENTS.md

## Project overview
This repository is KubePilot, an AI-powered Kubernetes operations project. The main areas are:

- `agent/` for orchestration and answer synthesis
- `rag/` for runbook loading, indexing, and retrieval
- `services/api/` for the FastAPI app
- `web/` for the frontend
- `tests/` for project validation

## Working conventions
- Keep changes minimal and focused on the root cause.
- Prefer small, surgical edits over broad refactors.
- Preserve the existing Python typing and style conventions.
- Follow the repository’s current module layout and naming patterns.

## Validation
Before completing work, run the relevant project checks:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
```

If a task changes API behavior, also validate the specific affected test path instead of making broad assumptions.

## Notes
- Python 3.11+ is required.
- The project uses `pytest` and `ruff` for verification.
- Keep documentation and code aligned when changing behavior.
