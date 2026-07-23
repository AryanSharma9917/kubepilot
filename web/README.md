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
- Unhealthy workload shortcuts
- Copilot chat with suggested prompts
- Deployment diagnosis for pods, events, logs, and recommendations
- Copyable incident markdown
- Recent trace and audit activity panels
