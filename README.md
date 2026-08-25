<p align="center">
  <img src="web/kubepilot-icon.svg" alt="KubePilot logo" width="96" />
</p>

<h1 align="center">KubePilot</h1>

<p align="center">
  An AI assistant for understanding and troubleshooting Kubernetes workloads.
</p>

<p align="center">
  <a href="#try-the-demo">Try the demo</a> ·
  <a href="#develop-locally">Develop locally</a> ·
  <a href="docs/runbooks/">Browse runbooks</a>
</p>

---

## What is KubePilot?

KubePilot gives Kubernetes operators one place to ask questions, inspect cluster
evidence, find relevant runbooks, diagnose deployments, and create incident
reports.

It is designed to support human decisions, not replace them. Answers are built
from observable signals and documented runbooks so an operator can review the
evidence behind a recommendation.

## Try the demo

### Requirements

- Git
- Docker Engine with the Docker Compose plugin

Check that Docker is installed and running:

```bash
docker --version
docker compose version
```

On a new computer, install Docker Desktop or Docker Engine first. Docker must
be running before you start KubePilot.

### First-time setup

Clone the repository and move into it:

```bash
git clone https://github.com/AryanSharma9917/kubepilot.git
cd kubepilot
```

You do not need to create a Python virtual environment for the Docker demo.
Docker installs the application dependencies while it builds the images.

### Start KubePilot

From the repository root, run this on the first launch:

```bash
docker compose up -d --build
```

The `--build` option creates the KubePilot images locally and downloads the
required base images. The first launch can take a few minutes. Later launches
can use `docker compose up -d` unless the source or Docker configuration changed.

Then open [http://127.0.0.1:3000](http://127.0.0.1:3000).

The demo includes a web console, FastAPI backend, Kubernetes inspection service,
Postgres, and predictable unhealthy workloads. No cloud account or Kubernetes
cluster is required for the default demo.

### Ask a question

Try any of these prompts in the console:

```text
Show unhealthy workloads
Why is checkout failing?
Why is email-worker pending?
How do I troubleshoot ImagePullBackOff?
Create an incident report for deployment checkout
```

### Check that it is working

```bash
./scripts/web-smoke.sh
```

Useful links:

- Web console: [http://127.0.0.1:3000](http://127.0.0.1:3000)
- API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- API health: [http://127.0.0.1:8000/healthz](http://127.0.0.1:8000/healthz)

Stop the demo with:

```bash
docker compose down
```

For a guided walkthrough, run `./scripts/demo.sh`. To try the same workflow on
a local kind cluster, run `./scripts/kind-demo.sh`.

## What KubePilot can do

- Answer Kubernetes operations questions through a chat interface
- Find relevant troubleshooting guidance in Markdown runbooks
- Inspect workload health, pods, events, and logs
- Diagnose common failures such as `CrashLoopBackOff`, `ImagePullBackOff`,
  readiness probe failures, and pending pods
- Generate JSON or Markdown incident reports with evidence and next actions
- Expose metrics, traces, and audit events for operational visibility
- Run with predictable fixtures locally or connect to a real Kubernetes cluster

## How it works

```text
Web console
    |
    v
FastAPI API
    |
    v
Agent workflow: route intent -> retrieve guidance -> inspect evidence -> answer
    |                         |
    v                         v
Runbook retrieval       Kubernetes tool service
                         (Go, fixture or real cluster mode)
```

The main building blocks are:

- `web/` - browser-based KubePilot console
- `services/api/` - FastAPI routes, authentication, audit, metrics, and tracing
- `agent/` - intent routing, workflow orchestration, tools, and answer synthesis
- `rag/` - runbook loading, chunking, indexing, retrieval, and evaluation
- `services/k8s-tool/` - Go service for Kubernetes inspection

## Develop locally

Python 3.11 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn kubepilot_api.main:app --reload
```

The API is then available at [http://127.0.0.1:8000](http://127.0.0.1:8000).
The interactive API reference is at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Run the checks with:

```bash
pytest
ruff check .
```

Optional dependency groups are available for real Kubernetes access, vector
retrieval, LangGraph, and OpenTelemetry. Install everything with:

```bash
python -m pip install -e ".[all]"
```

## Repository guide

| Path | Purpose |
| --- | --- |
| `docs/runbooks/` | Troubleshooting guidance used by retrieval |
| `demo/kubernetes/` | Intentionally unhealthy demo workloads |
| `helm/kubepilot/` | Helm chart for Kubernetes deployment |
| `gitops/argocd/` | Argo CD application manifests |
| `monitoring/` | Prometheus alerts and Grafana dashboard |
| `scripts/` | Demo and smoke-test workflows |
| `tests/` | API, agent, RAG, and Kubernetes tool tests |

## Deploying beyond the demo

The repository includes starter assets for Helm, Argo CD, Prometheus, and
Grafana. Before connecting KubePilot to a real cluster, review:

- [Real-cluster readiness](docs/real-cluster-readiness.md)
- [Production checklist](docs/production-checklist.md)
- [Security guidance](SECURITY.md)
- [GitOps setup](docs/gitops.md)

The default Compose setup uses Postgres for incident report artifacts. Without a
database URL, the API uses an in-memory store, which is useful for tests and
lightweight development.

## Project status

KubePilot is an active portfolio and experimentation project. The local fixture
demo is the easiest way to explore it. Production deployment, real-cluster
permissions, authentication, and observability still require environment-specific
configuration and review.

## License

See the repository for current licensing information.
