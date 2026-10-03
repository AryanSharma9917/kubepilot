# Hacktoberfest Weekend Challenge: Build for a Friend

This is a submission for the Hacktoberfest Weekend Challenge: Build for a Friend.

## What I built

KubePilot is an AI-powered Kubernetes operations assistant built for real-world
platform and on-call work. It helps an engineer ask questions in plain language,
retrieve the relevant operational knowledge from runbooks, inspect workload health,
review deployment issues, and generate evidence-based incident summaries.

Instead of forcing an operator to manually search through logs, docs, and YAML,
KubePilot brings the most likely troubleshooting evidence together in one place.

## Why this helps a friend

This is useful for someone who is supporting a Kubernetes service and needs a
quick, trustworthy starting point during a production incident. A friend or team
member can ask:

- Why is this deployment failing?
- What workloads are unhealthy?
- How do we troubleshoot this pod state?
- What evidence should I review before changing anything?

The project is intentionally designed to stay human-centered: it surfaces
sources, summarizes findings, and keeps remediation approval-gated rather than
executing destructive actions automatically.

## Why open-source AI matters here

Open-source and local-first AI is a better fit for Kubernetes operations than a
black-box cloud-only workflow because it keeps the decision path transparent and
controllable.

The local-first design allows:

- runbooks and retrieval to stay under the team's control
- operations to run without depending on a remote provider for every question
- evidence-based answers to be reviewed before action
- the project to be adapted to a friend or team with their own trusted workflows

This matters for operators working in sensitive, regulated, or access-restricted
infrastructure environments.

## What is in the project

- Chat and retrieval over Markdown runbooks
- Kubernetes workload and deployment health inspection
- Deployment diagnosis with pod, event, and log evidence
- Incident report generation with timeline and next actions
- API and policy controls for namespace and action restrictions
- Local demo and production-oriented deployment assets
- Helm profiles and smoke validation for safer deployment readiness checks

## How to run it

### Demo mode

```bash
docker compose up -d --build
```

Then open:

- http://127.0.0.1:3000
- http://127.0.0.1:8000/docs

### Local checks

```bash
source .venv/bin/activate
pytest -q
ruff check .
```

### Helm render validation

```bash
./scripts/helm-profile-smoke.sh
```

## Example prompts

```text
Show unhealthy workloads
Why is checkout failing?
Why is email-worker pending?
How do I troubleshoot ImagePullBackOff?
Create an incident report for deployment checkout
```

## Why this project is submission-ready

The repo has a real working local demo, a documented architecture, validation
coverage, and a clear operational story. It is not just a toy app; it is a
practical tool that would help a real person during an operational incident.

The project also deliberately stays grounded in evidence and operator review,
which fits the challenge theme of building something useful for a friend or
someone you care about.

## Project links

- Repository: https://github.com/AryanSharma9917/kubepilot
- Local demo: docker compose up -d --build
- Production readiness docs: docs/next-phase-roadmap.md
- Production deployment profile: docs/production-deployment-profile.md
