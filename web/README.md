# KubePilot Web

Static demo UI for KubePilot. It is served by Nginx in Docker Compose and calls
the FastAPI API through the same origin.

Run the full demo from the repository root:

```bash
docker compose up --build
```

Then open <http://127.0.0.1:3000>.

Start on **Overview**, then select **Investigate** next to an unhealthy workload.
The three primary navigation items are **Overview**, **Workloads**, and **Incidents**.
Workloads currently supports manual namespace/deployment entry; selecting a workload
on Overview fills these automatically. Diagnosis also generates the current incident
report, available under Incidents for copying or Markdown export.

The data-source notice distinguishes native fixtures from an inspection service
or cluster connection. The default Compose service uses fixtures. A service connection
is not proof of live cluster data. Failed connections show a retry instruction.

General chat, developer activity, and the guide are in **Help & tools**. Runtime
status and the capability map are collapsed under **Developer details** on Overview.
Existing hash routes remain supported.

The UI includes:

- Runtime status cards
- Live platform capability map
- Unhealthy workload shortcuts
- Copilot chat with suggested prompts
- Retrieved source cards and visible agent workflow steps
- Deployment diagnosis for pods, events, logs, recommendations, remediation plans, and copyable kubectl checks
- Incident room with severity, cause, impact, timeline, next actions, status copy, and markdown export
- Observability workspace with trace bars, audit filters, route groups, and agent activity
