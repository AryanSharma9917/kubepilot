# KubePilot Web

Static demo UI for KubePilot. It is served by Nginx in Docker Compose and calls
the FastAPI API through the same origin.

Run the full demo from the repository root:

```bash
docker compose up --build
```

Then open <http://127.0.0.1:3000>.

The UI includes:

- Runtime status cards
- Live platform capability map
- Unhealthy workload shortcuts
- Copilot chat with suggested prompts
- Retrieved source cards and visible agent workflow steps
- Deployment diagnosis for pods, events, logs, recommendations, and copyable kubectl checks
- Incident room with severity, cause, impact, timeline, next actions, status copy, and markdown export
- Observability workspace with trace bars, audit filters, route groups, and agent activity
