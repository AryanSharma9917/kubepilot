# KubePilot Web

A static console for investigating Kubernetes failures and sharing evidence snapshots.
The main journey is **Overview → Workloads → Incidents**. General chat, the guided
walkthrough, and developer activity are under **Help & tools**.

## Run locally

For the full fixture demo, from the repository root:

```bash
docker compose up --build
```

For native development, use Python 3.11+ and Node.js 20+. From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/uvicorn kubepilot_api.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
node web/dev-server.cjs
```

The UI listens on port 3000 and forwards API requests to port 8000. Set
`KUBEPILOT_WEB_PORT` or `KUBEPILOT_API_URL` to use different ports. The server binds
only to loopback and is intended for local development. It serves the static UI;
source changes appear on browser refresh. It needs no npm dependencies. Compose
serves the same assets with Nginx and includes Postgres and the Go inspection service.

## Walk through the demo

1. On **Overview**, choose **Investigate** for `payments/checkout`.
2. Review the observed problem, failure signals, pod/event/log evidence, explained
   read-only checks, and verification guidance. Recommendations are not executed.
3. Choose **Ask about this workload**, then **Explain this failure**. The attached
   namespace and deployment are visible. **Clear workload context** before asking
   about a different workload; the picker returns to Workloads.
4. Return to **Workloads**, then select **Create incident report**. Creation collects
   a fresh backend snapshot; it does not reuse the earlier diagnosis as live evidence.
5. In **Incidents**, select a saved report, copy its status update, or download
   Markdown. Export uses the saved report ID; it does not create another artifact.

Repeat with `platform/metrics-scraper` for readiness failures and
`notifications/email-worker` for pending pods. Fixtures remain unhealthy by design.
The data-source notice distinguishes fixtures from a configured inspection service
or cluster connection. An inspection service can itself use fixtures.

Selections persist while switching views, not across reloads. Reports are stored by
the API: native in-memory reports disappear on API restart; Compose uses Postgres.
The report list shows up to 100 recent snapshots and can be refreshed. Copy/download
controls remain disabled until content is available. Clipboard errors offer manual
copy or download. Sources without excerpts are labelled accordingly; runbook matches
do not establish the cause of a failure. Chat has no conversation memory.

Keyboard users can skip to the main content, activate navigation with Enter, and
follow focus to the destination heading. Browser Back/Forward navigates views.
Reduced-motion preferences disable animation. Optional developer activity failures
do not prevent the workload list from loading. Failed workload requests offer Refresh;
a missing deployment offers a retry after checking the names.

## Run checks

The dependency-free rendering and request-state checks need Node.js only:

```bash
node web/checks/investigation.cjs
node web/checks/chat.cjs
node web/checks/incidents.cjs
```

For browser coverage, install the pinned browser tooling:

```bash
cd web
npm ci
npx playwright install chromium
npm run check
npm run check:browser
```

On a Linux machine missing browser system libraries, use
`npx playwright install --with-deps chromium`. To use an existing compatible Chromium,
set `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` to its executable path.

The browser suite starts and stops its own fixture FastAPI process and development
server on ephemeral ports. Install the root Python dev dependencies first. It uses
`.venv/bin/python` when present, otherwise `python3`; override with `KUBEPILOT_PYTHON`.
No external cluster, LLM, database, or pre-running UI process is needed. The suite
uses an isolated in-memory report store. Set `KUBEPILOT_SCREENSHOT_DIR` to capture
screenshots outside the checkout or in an ignored output directory.

Coverage includes all three fixture investigations, contextual chat, citations,
explicit report creation, reopening saved reports, clipboard and same-ID Markdown
downloads, keyboard entry, navigation history, malformed hashes, reduced motion,
optional activity failures, retry, and missing deployments. Layout checks cover
Overview, Workloads, chat, and Incidents at desktop/mobile widths in light/dark themes.
The Web workflow in GitHub Actions runs the same checks. This validates the fixture
workflow; real-cluster permissions, production security, and deployments need separate
validation.

## API additions

Both `/api/v1/chat` and `/api/v1/chat/stream` accept optional
`workload: {namespace, deployment}` context alongside `message`. Message-only requests
remain supported. Context scopes reference extraction; not every question invokes
Kubernetes tools.

Saved Markdown is available from
`GET /api/v1/cluster/incident-reports/{report_id}/markdown`.

## Development-cluster connection guide

Open **Help & tools → Cluster connection** for configuration steps and a named
namespace check. The result distinguishes fixture data from deployment reads and
shows when the check completed. It does not verify all RBAC permissions or discover
cluster identity. Set `KUBEPILOT_CLUSTER_DISPLAY_NAME` on the API host for a display
label; never paste kubeconfigs or tokens into the UI.

Use a namespace-scoped read-only credential for the pilot. Overview and general
cluster-health chat can still request cluster-wide deployment lists; they may fail
with namespace-only permissions. Use the namespace check and manual Workloads entry.
The application allowlist is not a replacement for Kubernetes RBAC. See
[Real-cluster readiness](../docs/real-cluster-readiness.md) for permission examples,
current limitations, and the remaining live-cluster validation steps.
