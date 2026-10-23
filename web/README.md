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
on Overview fills these automatically. Choose **Create incident report** after diagnosis to save a snapshot,
available under Incidents for copying or Markdown export.

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

### Guided workload investigations

Open **Workloads** to choose from workloads needing attention, or enter a namespace
and deployment manually. Selecting **Investigate** on Overview opens the same workflow.
The selected deployment remains in the form when switching views during the session.
Investigations show the observed problem, suggested cause, pod/event/log evidence,
next checks, and verification guidance. Review suggested causes against the evidence;
KubePilot does not execute the displayed commands. **Refresh investigation** collects
another diagnosis snapshot, and **Create incident report** saves a handoff snapshot.
Demo fixtures remain unhealthy by design. Selection is not persisted across page reloads.

Run dependency-free investigation rendering and request-order checks with
`node web/checks/investigation.cjs` from the repository root. These complement
the Python suite; they do not replace browser interaction or layout checks.

### Ask about the selected workload

After starting an investigation, choose **Ask about this workload**. Chat shows the
attached namespace and deployment, and offers questions about its failure or status.
Use **Clear workload context** for general questions or before asking about another
workload. The workload picker icon returns to Workloads to change the selection.
Each submitted message records its workload label, so changing the selection does
not change the meaning of earlier messages. Only one chat request runs at a time.

Chat separates observed evidence from suggested checks where the response provides
those sections. Runbook excerpts appear alongside the answer; source titles without
excerpts are labelled accordingly. Runbooks are guidance, not proof of the cause.
Read-only command cards explain their purpose and limitations. Commands are copied
for operator review, never executed by the browser.

The chat API accepts an optional `workload` object containing `namespace` and
`deployment` on both `/api/v1/chat` and `/api/v1/chat/stream`. Existing message-only
requests continue to work. Workload context scopes reference extraction; it does not
add conversation memory or guarantee that every question invokes Kubernetes tools.

Run `node web/checks/chat.cjs` for context payload, duplicate-request, failure-recovery,
source-label, and command-explanation checks. The integrated browser workflow was
also checked against the local API for contextual diagnosis and cited runbook answers,
with Overview checked at desktop and mobile widths.

### Incident handoffs

Diagnosis does not save an incident report automatically. Choose **Create incident
report** in the investigation to save a report from the current backend evidence.
**Incidents** lists up to 100 recent saved reports with severity, time, and ID.
Choose a report to review its details, copy a stakeholder update, copy Markdown,
or download a `.md` file. Copy and download controls stay disabled until their
content is loaded. Clipboard errors offer manual-copy and download alternatives.

Markdown export uses the selected saved report ID; exporting does not regenerate
evidence or create a second report. Reports are snapshots, not live incident state.
The default native development store is in memory and resets with the API process;
the Compose configuration uses Postgres. Refresh reports after another user creates
one. Empty lists and failed requests include instructions for the next step.

Saved Markdown is available at
`GET /api/v1/cluster/incident-reports/{report_id}/markdown`.

Run `node web/checks/incidents.cjs` to verify artifact selection, stale-response
protection, export controls, and error recovery. Browser validation also exercised
explicit creation, reopening a saved report after reload, clipboard copying, and
a Markdown download containing the same report ID at desktop and mobile widths.
