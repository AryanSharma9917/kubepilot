const API_BASE = "";

const appShell = document.querySelector("#appShell");
const collapseButton = document.querySelector("#collapseButton");
const themeToggle = document.querySelector("#themeToggle");
const connectionStatus = document.querySelector("#connectionStatus");
const refreshButton = document.querySelector("#refreshButton");
const statusCards = document.querySelector("#statusCards");
const capabilityGrid = document.querySelector("#capabilityGrid");
const workloadList = document.querySelector("#workloadList");
const traceList = document.querySelector("#traceList");
const auditList = document.querySelector("#auditList");
const observabilitySummary = document.querySelector("#observabilitySummary");
const auditFilter = document.querySelector("#auditFilter");
const auditRouteGroups = document.querySelector("#auditRouteGroups");
const agentActivity = document.querySelector("#agentActivity");
const chatForm = document.querySelector("#chatForm");
const chatInput = document.querySelector("#chatInput");
const chatLog = document.querySelector("#chatLog");
const ragModeBadge = document.querySelector("#ragModeBadge");
const retrievedSources = document.querySelector("#retrievedSources");
const diagnosisForm = document.querySelector("#diagnosisForm");
const namespaceInput = document.querySelector("#namespaceInput");
const deploymentInput = document.querySelector("#deploymentInput");
const diagnosisOutput = document.querySelector("#diagnosisOutput");
const incidentTitle = document.querySelector("#incidentTitle");
const incidentSummary = document.querySelector("#incidentSummary");
const incidentSeverity = document.querySelector("#incidentSeverity");
const incidentCause = document.querySelector("#incidentCause");
const incidentImpact = document.querySelector("#incidentImpact");
const incidentResource = document.querySelector("#incidentResource");
const incidentStatusUpdate = document.querySelector("#incidentStatusUpdate");
const incidentTimeline = document.querySelector("#incidentTimeline");
const incidentActions = document.querySelector("#incidentActions");
const incidentMarkdown = document.querySelector("#incidentMarkdown");
const copyMarkdownButton = document.querySelector("#copyMarkdownButton");
const copyStatusButton = document.querySelector("#copyStatusButton");
const copyButtons = document.querySelectorAll("[data-copy]");
const heroTyped = document.querySelector("#heroTyped");
const copilotTyped = document.querySelector("#copilotTyped");

let latestSpans = [];
let latestAuditEvents = [];
let typedPhraseIndex = 0;

const TYPED_PHRASES = [
  "scanning cluster signals",
  "retrieving runbook context",
  "building incident evidence",
  "planning safe remediation",
];

const ICONS = {
  copy: '<svg><use href="#i-copy"></use></svg>',
  check: '<svg><use href="#i-check"></use></svg>',
  search: '<svg><use href="#i-search"></use></svg>',
};

function setIconButtonIcon(button, iconName, label) {
  const iconElement = button.querySelector(".icon");
  if (iconElement) {
    iconElement.innerHTML = ICONS[iconName] || iconName;
  } else {
    button.textContent = label;
  }
  button.setAttribute("aria-label", label);
  button.setAttribute("title", label);
}

function setConnectionStatus(message, state = "") {
  connectionStatus.textContent = message;
  connectionStatus.className = `connection-pill ${state}`.trim();
}

function openView(viewName) {
  document.querySelectorAll("[data-view-panel]").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.viewPanel === viewName);
  });
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === viewName);
  });
}

function getKnownView(viewName) {
  const view = document.querySelector(`[data-view-panel="${viewName}"]`);
  return view ? viewName : "copilot";
}

function openViewFromHash() {
  const viewName = getKnownView(window.location.hash.replace("#", ""));
  openView(viewName);
}

function setViewHash(viewName) {
  const nextHash = `#${getKnownView(viewName)}`;
  if (window.location.hash !== nextHash) {
    window.history.replaceState(null, "", nextHash);
  }
  openViewFromHash();
}

function setTheme(theme) {
  document.body.dataset.theme = theme;
  localStorage.setItem("kubepilot-theme", theme);
  const nextTheme = theme === "dark" ? "light" : "dark";
  if (themeToggle) {
    themeToggle.setAttribute("aria-label", `Switch to ${nextTheme} mode`);
    themeToggle.setAttribute("title", `Switch to ${nextTheme} mode`);
  }
}

function bootTheme() {
  const savedTheme = localStorage.getItem("kubepilot-theme");
  const prefersLight = window.matchMedia("(prefers-color-scheme: light)").matches;
  setTheme(savedTheme || (prefersLight ? "light" : "dark"));
}

function startTypeReadout() {
  const renderPhrase = () => {
    const phrase = TYPED_PHRASES[typedPhraseIndex % TYPED_PHRASES.length];
    if (heroTyped) {
      heroTyped.textContent = phrase;
    }
    if (copilotTyped) {
      copilotTyped.textContent = phrase.replaceAll(" ", "_");
    }
    typedPhraseIndex += 1;
  };
  renderPhrase();
  setInterval(renderPhrase, 2400);
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "content-type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!response.ok) {
    const detail = await safeErrorDetail(response);
    throw new Error(detail || `${response.status} ${response.statusText}`);
  }
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

async function safeErrorDetail(response) {
  try {
    const payload = await response.json();
    return payload.detail;
  } catch {
    return response.statusText;
  }
}

async function loadOverview() {
  setConnectionStatus("Connecting", "");
  refreshButton.disabled = true;
  try {
    const [status, capabilities, health, traces, audit] = await Promise.all([
      apiFetch("/api/v1/status"),
      apiFetch("/api/v1/capabilities"),
      apiFetch("/api/v1/cluster/health"),
      apiFetch("/api/v1/traces?limit=6"),
      apiFetch("/api/v1/audit/events?limit=8"),
    ]);
    renderStatus(status);
    renderCapabilities(capabilities.capabilities || []);
    renderWorkloads(health);
    latestSpans = traces.spans || [];
    latestAuditEvents = audit.events || [];
    renderObservability();
    setConnectionStatus("API connected", "ok");
  } catch (error) {
    setConnectionStatus("API unavailable", "error");
    capabilityGrid.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    workloadList.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  } finally {
    refreshButton.disabled = false;
  }
}

function renderCapabilities(capabilities) {
  if (!capabilities.length) {
    capabilityGrid.innerHTML = `<div class="empty-state">No platform capabilities returned.</div>`;
    return;
  }
  capabilityGrid.innerHTML = capabilities
    .map(
      (capability) => `
        <article class="capability-card">
          <div>
            <strong>${escapeHtml(capability.name)}</strong>
            <span>${escapeHtml(capability.status)}</span>
          </div>
          <p>${escapeHtml(capability.description)}</p>
        </article>
      `,
    )
    .join("");
}

function renderObservability() {
  renderObservabilitySummary(latestSpans, latestAuditEvents);
  renderTraces(latestSpans);
  renderRouteGroups(latestAuditEvents);
  renderAuditEvents(latestAuditEvents);
  renderAgentActivity(latestAuditEvents);
}

function renderObservabilitySummary(spans, events) {
  const averageDuration = spans.length
    ? spans.reduce((total, span) => total + span.duration_ms, 0) / spans.length
    : 0;
  const errorCount = events.filter((event) => event.status_code >= 400).length;
  const chatCount = events.filter((event) => event.path.includes("/chat")).length;
  const cards = [
    ["Trace spans", spans.length],
    ["Avg duration", `${averageDuration.toFixed(2)} ms`],
    ["Errors", errorCount],
    ["Chat calls", chatCount],
  ];
  observabilitySummary.innerHTML = cards
    .map(
      ([label, value]) => `
        <div class="obs-card">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(String(value))}</strong>
        </div>
      `,
    )
    .join("");
}

function renderStatus(status) {
  ragModeBadge.textContent = `RAG: ${status.rag_mode}`;
  ragModeBadge.className = `rag-mode-badge ${status.rag_mode}`;
  const cards = [
    ["Environment", status.environment],
    ["Kubernetes", status.kubernetes_mode],
    ["RAG", status.rag_mode],
    ["Agent", status.agent_mode],
    ["Auth", status.auth_enabled ? "enabled" : "off"],
    ["Rate limit", status.rate_limit_per_minute ? `${status.rate_limit_per_minute}/min` : "off"],
  ];
  statusCards.innerHTML = cards
    .map(
      ([label, value]) => `
        <div class="stat-card">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(String(value))}</strong>
        </div>
      `,
    )
    .join("");
}

function renderWorkloads(health) {
  if (!health.workloads?.length) {
    workloadList.innerHTML = `<div class="empty-state">No unhealthy workloads found.</div>`;
    return;
  }
  workloadList.innerHTML = health.workloads
    .map(
      (workload) => `
        <div class="workload-card">
          <div>
            <strong>${escapeHtml(workload.namespace)}/${escapeHtml(workload.kind.toLowerCase())}/${escapeHtml(workload.name)}</strong>
            <span>${escapeHtml(workload.reason)}</span>
          </div>
          <button
            class="workload-action"
            type="button"
            data-namespace="${escapeHtml(workload.namespace)}"
            data-deployment="${escapeHtml(workload.name)}"
          >
            <span class="button-icon"><svg><use href="#i-search"></use></svg></span>
            <span>${workload.ready_replicas}/${workload.desired_replicas}</span>
          </button>
        </div>
      `,
    )
    .join("");
}

function renderTraces(spans) {
  if (!spans.length) {
    traceList.innerHTML = `<div class="empty-state">Trace spans will appear after API calls.</div>`;
    return;
  }
  traceList.innerHTML = spans
    .map(
      (span) => {
        const width = Math.min(100, Math.max(8, span.duration_ms * 18));
        return `
        <div class="trace-row">
          <div>
            <strong>${escapeHtml(span.name)}</strong>
            <div class="trace-meter"><span style="width: ${width}%"></span></div>
          </div>
          <span>${span.duration_ms.toFixed(2)} ms</span>
        </div>
      `;
      },
    )
    .join("");
}

function renderAuditEvents(events) {
  const query = auditFilter.value.trim().toLowerCase();
  const visibleEvents = query
    ? events.filter((event) => {
        const haystack = `${event.method} ${event.path} ${event.status_code}`.toLowerCase();
        return haystack.includes(query);
      })
    : events;
  if (!visibleEvents.length) {
    auditList.innerHTML = `<div class="empty-state">Audit events will appear after API calls.</div>`;
    return;
  }
  auditList.innerHTML = visibleEvents
    .map(
      (event) => `
        <div class="audit-row">
          <div>
            <strong>${escapeHtml(event.method)} ${escapeHtml(event.path)}</strong>
            <small>${formatTime(event.timestamp)} - ${escapeHtml(event.request_id.slice(0, 8))}</small>
          </div>
          <span class="${event.status_code >= 400 ? "status-error" : ""}">${event.status_code}</span>
        </div>
      `,
    )
    .join("");
}

function renderRouteGroups(events) {
  if (!events.length) {
    auditRouteGroups.innerHTML = `<div class="empty-state compact">Route groups will appear after API calls.</div>`;
    return;
  }
  const groups = events.reduce((accumulator, event) => {
    const key = `${event.method} ${event.path}`;
    const current = accumulator.get(key) || { count: 0, failures: 0 };
    current.count += 1;
    current.failures += event.status_code >= 400 ? 1 : 0;
    accumulator.set(key, current);
    return accumulator;
  }, new Map());
  auditRouteGroups.innerHTML = [...groups.entries()]
    .slice(0, 4)
    .map(
      ([route, summary]) => `
        <div class="route-pill">
          <strong>${escapeHtml(route)}</strong>
          <span>${summary.count} call${summary.count === 1 ? "" : "s"}${summary.failures ? ` / ${summary.failures} failing` : ""}</span>
        </div>
      `,
    )
    .join("");
}

function renderAgentActivity(events) {
  const interestingEvents = events.filter(
    (event) =>
      event.path.includes("/chat") ||
      event.path.includes("/diagnose") ||
      event.path.includes("/incident-report"),
  );
  if (!interestingEvents.length) {
    agentActivity.innerHTML = `<div class="empty-state compact">Ask KubePilot or run a diagnosis to see the API trail.</div>`;
    return;
  }
  agentActivity.innerHTML = interestingEvents
    .slice(0, 5)
    .map(
      (event, index) => `
        <div class="agent-step">
          <span>${index + 1}</span>
          <div>
            <strong>${escapeHtml(activityLabel(event.path))}</strong>
            <small>${escapeHtml(event.method)} ${escapeHtml(event.path)} - ${event.status_code} - ${formatTime(event.timestamp)}</small>
          </div>
        </div>
      `,
    )
    .join("");
}

function activityLabel(path) {
  if (path.includes("/chat")) {
    return "Agent answered the operator";
  }
  if (path.includes("/diagnose")) {
    return "Kubernetes diagnosis collected evidence";
  }
  if (path.includes("/incident-report")) {
    return "Incident report generated";
  }
  return "API activity recorded";
}

function formatTime(timestamp) {
  return new Date(timestamp * 1000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

async function sendChat(message) {
  openView("copilot");
  chatInput.disabled = true;
  appendChatMessage(message, "user");
  appendChatMessage("Thinking through runbooks and cluster signals...", "assistant", true);
  try {
    const response = await apiFetch("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    replacePendingAssistant(renderChatAnswer(response));
    await loadOverview();
  } catch (error) {
    replacePendingAssistant(`<div class="error-text">${escapeHtml(error.message)}</div>`);
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
  }
}

function renderChatAnswer(response) {
  const sources = response.sources?.length
    ? `
      <div class="source-list">
        ${response.sources
          .map(
            (source) => `
              <span>
                <svg><use href="#i-book"></use></svg>
                ${escapeHtml(source)}
              </span>
            `,
          )
          .join("")}
      </div>
    `
    : "";
  const citations = response.citations?.length
    ? `
      <div class="citation-list">
        ${response.citations
          .map(
            (citation) => `
              <details>
                <summary>${escapeHtml(citation.title)}</summary>
                <p>${escapeHtml(citation.snippet)}</p>
                <small>${escapeHtml(citation.source)}</small>
              </details>
            `,
          )
          .join("")}
      </div>
    `
    : "";
  const workflow = response.workflow_steps?.length
    ? `
      <div class="workflow-panel">
        <div class="workflow-title">
          <span class="button-icon"><svg><use href="#i-command"></use></svg></span>
          <strong>Agent Steps</strong>
        </div>
        <div class="workflow-steps">
          ${response.workflow_steps
            .map(
              (step, index) => `
                <div class="workflow-step-card">
                  <span>${index + 1}</span>
                  <div>
                    <strong>${escapeHtml(step.name.replaceAll("_", " "))}</strong>
                    <p>${escapeHtml(step.description)}</p>
                  </div>
                  <small>${escapeHtml(step.status)}</small>
                </div>
              `,
            )
            .join("")}
        </div>
      </div>
    `
    : "";
  renderRetrievedSources(response.sources || [], response.citations || []);
  return `
    <div>${escapeHtml(response.answer)}</div>
    ${workflow}
    ${sources}
    ${citations}
  `;
}

function renderRetrievedSources(sources, citations) {
  if (!sources.length && !citations.length) {
    retrievedSources.innerHTML = `<span>No retrieved sources for this answer.</span>`;
    return;
  }
  const cards = citations.length
    ? citations.map((citation) => ({
        title: citation.title,
        source: citation.source,
        snippet: citation.snippet,
      }))
    : sources.map((source) => ({
        title: source,
        source,
        snippet: "Retrieved by the configured KubePilot runbook retriever.",
      }));
  retrievedSources.innerHTML = cards
    .slice(0, 4)
    .map(
      (card) => `
        <article class="retrieved-source-card">
          <strong>${escapeHtml(card.title)}</strong>
          <p>${escapeHtml(card.snippet)}</p>
          <small>${escapeHtml(card.source)}</small>
        </article>
      `,
    )
    .join("");
}

function appendChatMessage(content, role, pending = false) {
  const message = document.createElement("div");
  message.className = role === "user" ? "user-message" : "assistant-message";
  if (pending) {
    message.dataset.pending = "true";
  }
  message.innerHTML = escapeHtml(content);
  chatLog.append(message);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function replacePendingAssistant(html) {
  const pending = chatLog.querySelector("[data-pending='true']");
  if (!pending) {
    return;
  }
  delete pending.dataset.pending;
  pending.innerHTML = html;
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function diagnoseDeployment(namespace, deployment) {
  openView("diagnosis");
  const submitButton = diagnosisForm.querySelector("button[type='submit']");
  submitButton.disabled = true;
  diagnosisOutput.innerHTML = `<div class="empty-state">Collecting pods, events, and logs...</div>`;
  incidentMarkdown.textContent = "Generating markdown report...";
  try {
    const encodedNamespace = encodeURIComponent(namespace);
    const encodedDeployment = encodeURIComponent(deployment);
    const [diagnosis, report, remediation, markdown] = await Promise.all([
      apiFetch(
        `/api/v1/cluster/namespaces/${encodedNamespace}/deployments/${encodedDeployment}/diagnose`,
      ),
      apiFetch(
        `/api/v1/cluster/namespaces/${encodedNamespace}/deployments/${encodedDeployment}/incident-report`,
      ),
      apiFetch(
        `/api/v1/cluster/namespaces/${encodedNamespace}/deployments/${encodedDeployment}/remediation-plan`,
      ),
      apiFetch(
        `/api/v1/cluster/namespaces/${encodedNamespace}/deployments/${encodedDeployment}/incident-report.md`,
      ),
    ]);
    renderDiagnosis(diagnosis, remediation);
    renderIncidentReport(report);
    incidentMarkdown.textContent = markdown;
    await loadOverview();
  } catch (error) {
    diagnosisOutput.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    renderIncidentError(error.message);
    incidentMarkdown.textContent = "Incident report unavailable.";
  } finally {
    submitButton.disabled = false;
  }
}

function renderIncidentReport(report) {
  incidentTitle.textContent = report.title;
  incidentSummary.textContent = report.summary;
  incidentSeverity.textContent = report.severity;
  incidentSeverity.className = `severity-badge ${report.severity}`;
  incidentCause.textContent = report.probable_cause;
  incidentImpact.textContent = report.operator_impact;
  incidentResource.textContent = report.impacted_resource;
  incidentStatusUpdate.textContent = report.status_update;
  incidentTimeline.innerHTML = report.timeline?.length
    ? report.timeline
        .map(
          (item) => `
            <div class="timeline-item">
              <span>${escapeHtml(item.source)}</span>
              <p>${escapeHtml(item.message)}</p>
            </div>
          `,
        )
        .join("")
    : `<div class="empty-state compact">No timeline evidence returned.</div>`;
  incidentActions.innerHTML = report.next_actions?.length
    ? report.next_actions
        .map(
          (action) => `
            <label class="action-item">
              <span class="check-dot"><svg><use href="#i-check"></use></svg></span>
              <span>${escapeHtml(action)}</span>
            </label>
          `,
        )
        .join("")
    : `<div class="empty-state compact">No next actions returned.</div>`;
}

function renderIncidentError(message) {
  incidentTitle.textContent = "Incident report unavailable";
  incidentSummary.textContent = message;
  incidentSeverity.textContent = "Error";
  incidentSeverity.className = "severity-badge critical";
  incidentCause.textContent = "KubePilot could not generate the structured incident report.";
  incidentImpact.textContent = "The diagnosis view may still contain partial evidence.";
  incidentResource.textContent = "Unavailable";
  incidentStatusUpdate.textContent = "Incident status update unavailable.";
  incidentTimeline.innerHTML = `<div class="empty-state compact">No timeline available.</div>`;
  incidentActions.innerHTML = `<div class="empty-state compact">Retry the diagnosis after the API recovers.</div>`;
}

function renderDiagnosis(diagnosis, remediation) {
  const commands = buildDiagnosisCommands(diagnosis);
  const podRows = diagnosis.pods
    .map(
      (pod) => `
        <tr>
          <td>${escapeHtml(pod.name)}</td>
          <td>${escapeHtml(pod.phase)}</td>
          <td>${pod.ready ? "Ready" : "Not ready"}</td>
          <td>${pod.restart_count}</td>
          <td>${escapeHtml(pod.reason || "-")}</td>
        </tr>
      `,
    )
    .join("");
  const eventItems = diagnosis.events
    .map((event) => `<li><strong>${escapeHtml(event.reason)}:</strong> ${escapeHtml(event.message)}</li>`)
    .join("");
  const logItems = diagnosis.logs
    .map(
      (log) => `
        <li>
          <strong>${escapeHtml(log.pod_name)} / ${escapeHtml(log.container_name)}</strong>
          <code>${escapeHtml(log.text)}</code>
        </li>
      `,
    )
    .join("");
  const recommendations = diagnosis.recommendations
    .map((recommendation) => `<li>${escapeHtml(recommendation)}</li>`)
    .join("");
  diagnosisOutput.innerHTML = `
    <div class="diagnosis-summary">
      <strong>${escapeHtml(diagnosis.namespace)}/deployment/${escapeHtml(diagnosis.name)}</strong>
      <span>${escapeHtml(diagnosis.health.status)}: ${escapeHtml(diagnosis.health.reason)}</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Pod</th>
            <th>Phase</th>
            <th>Ready</th>
            <th>Restarts</th>
            <th>Reason</th>
          </tr>
        </thead>
        <tbody>${podRows}</tbody>
      </table>
    </div>
    <div class="diagnosis-lists">
      <section>
        <h3>Events</h3>
        <ul>${eventItems || "<li>No events found.</li>"}</ul>
      </section>
      <section>
        <h3>Logs</h3>
        <ul>${logItems || "<li>No logs captured.</li>"}</ul>
      </section>
      <section>
        <h3>Recommendations</h3>
        <ul>${recommendations || "<li>No recommendations.</li>"}</ul>
      </section>
    </div>
    ${renderRemediationPlan(remediation)}
    <section class="command-palette">
      <div class="card-title-row">
        <div>
          <p class="eyebrow">Operator Commands</p>
          <h3>Safe read-only checks</h3>
        </div>
      </div>
      <div class="command-grid">
        ${commands
          .map(
            (command) => `
              <article class="command-card">
                <div>
                  <strong>${escapeHtml(command.label)}</strong>
                  <button
                    class="secondary-button icon-button"
                    type="button"
                    data-copy-dynamic="${escapeHtml(command.value)}"
                    aria-label="Copy ${escapeHtml(command.label)}"
                    title="Copy ${escapeHtml(command.label)}"
                  >
                    <span class="icon"><svg><use href="#i-copy"></use></svg></span>
                  </button>
                </div>
                <code>${escapeHtml(command.value)}</code>
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderRemediationPlan(plan) {
  if (!plan) {
    return "";
  }
  return `
    <section class="remediation-panel">
      <div class="card-title-row">
        <div>
          <p class="eyebrow">Remediation</p>
          <h3>Approval-gated action plan</h3>
        </div>
        <span class="approval-badge">${plan.approval_required ? "Approval required" : "Read only"}</span>
      </div>
      <p class="remediation-summary">${escapeHtml(plan.summary)}</p>
      <div class="remediation-grid">
        ${plan.actions
          .map(
            (action) => `
              <article class="remediation-card">
                <div class="remediation-card-head">
                  <strong>${escapeHtml(action.title)}</strong>
                  <span class="risk-badge ${escapeHtml(action.risk)}">${escapeHtml(action.risk)}</span>
                </div>
                <p>${escapeHtml(action.reason)}</p>
                <div class="command-line">
                  <code>${escapeHtml(action.command)}</code>
                  <button
                    class="secondary-button icon-button"
                    type="button"
                    data-copy-dynamic="${escapeHtml(action.command)}"
                    aria-label="Copy ${escapeHtml(action.title)}"
                    title="Copy ${escapeHtml(action.title)}"
                  >
                    <span class="icon"><svg><use href="#i-copy"></use></svg></span>
                  </button>
                </div>
              </article>
            `,
          )
          .join("")}
      </div>
      <div class="rollback-row">
        <strong>Rollback</strong>
        <code>${escapeHtml(plan.rollback)}</code>
        <button
          class="secondary-button icon-button"
          type="button"
          data-copy-dynamic="${escapeHtml(plan.rollback)}"
          aria-label="Copy rollback command"
          title="Copy rollback command"
        >
          <span class="icon"><svg><use href="#i-copy"></use></svg></span>
        </button>
      </div>
    </section>
  `;
}

function buildDiagnosisCommands(diagnosis) {
  const namespace = diagnosis.namespace;
  const deployment = diagnosis.name;
  const firstPod = diagnosis.pods[0]?.name || `<pod-name>`;
  return [
    {
      label: "Rollout status",
      value: `kubectl rollout status deployment/${deployment} -n ${namespace}`,
    },
    {
      label: "Describe deployment",
      value: `kubectl describe deployment/${deployment} -n ${namespace}`,
    },
    {
      label: "List pods",
      value: `kubectl get pods -n ${namespace} -l app=${deployment} -o wide`,
    },
    {
      label: "Recent events",
      value: `kubectl get events -n ${namespace} --sort-by=.lastTimestamp`,
    },
    {
      label: "Pod logs",
      value: `kubectl logs ${firstPod} -n ${namespace} --tail=80`,
    },
  ];
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return entities[character];
  });
}

function boot() {
  bootTheme();
  startTypeReadout();
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      setTheme(document.body.dataset.theme === "dark" ? "light" : "dark");
    });
  }
  collapseButton.addEventListener("click", () => {
    appShell.classList.toggle("sidebar-collapsed");
    const collapsed = appShell.classList.contains("sidebar-collapsed");
    collapseButton.setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
    collapseButton.setAttribute("title", collapsed ? "Expand sidebar" : "Collapse sidebar");
  });
  refreshButton.addEventListener("click", () => {
    loadOverview();
  });
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      setViewHash(button.dataset.view);
    });
  });
  document.querySelectorAll("[data-open-view]").forEach((button) => {
    button.addEventListener("click", () => {
      setViewHash(button.dataset.openView);
    });
  });
  window.addEventListener("hashchange", openViewFromHash);
  openViewFromHash();
  workloadList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-namespace][data-deployment]");
    if (!button) {
      return;
    }
    namespaceInput.value = button.dataset.namespace;
    deploymentInput.value = button.dataset.deployment;
    diagnoseDeployment(button.dataset.namespace, button.dataset.deployment);
  });
  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
      chatInput.value = button.dataset.prompt;
      sendChat(button.dataset.prompt);
    });
  });
  copyMarkdownButton.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(incidentMarkdown.textContent);
      setIconButtonIcon(copyMarkdownButton, "check", "Copied markdown report");
      setTimeout(() => {
        setIconButtonIcon(copyMarkdownButton, "copy", "Copy markdown report");
      }, 1600);
    } catch {
      setIconButtonIcon(copyMarkdownButton, "!", "Copy failed");
    }
  });
  copyStatusButton.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(incidentStatusUpdate.textContent);
      setIconButtonIcon(copyStatusButton, "check", "Copied status update");
      setTimeout(() => {
        setIconButtonIcon(copyStatusButton, "copy", "Copy status update");
      }, 1600);
    } catch {
      setIconButtonIcon(copyStatusButton, "!", "Copy failed");
    }
  });
  copyButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(button.dataset.copy);
        setIconButtonIcon(button, "check", "Copied");
        setTimeout(() => {
          setIconButtonIcon(button, "copy", "Copy");
        }, 1400);
      } catch {
        setIconButtonIcon(button, "!", "Copy failed");
      }
    });
  });
  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy-dynamic]");
    if (!button) {
      return;
    }
    try {
      await navigator.clipboard.writeText(button.dataset.copyDynamic);
      setIconButtonIcon(button, "check", "Copied");
      setTimeout(() => {
        setIconButtonIcon(button, "copy", "Copy");
      }, 1400);
    } catch {
      setIconButtonIcon(button, "!", "Copy failed");
    }
  });
  auditFilter.addEventListener("input", () => {
    renderAuditEvents(latestAuditEvents);
  });
  chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const message = chatInput.value.trim();
    if (!message) {
      return;
    }
    chatInput.value = "";
    sendChat(message);
  });
  diagnosisForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const namespace = namespaceInput.value.trim();
    const deployment = deploymentInput.value.trim();
    if (!namespace || !deployment) {
      return;
    }
    diagnoseDeployment(namespace, deployment);
  });
  loadOverview();
}

boot();
