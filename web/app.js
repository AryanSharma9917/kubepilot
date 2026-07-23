const API_BASE = "";

const connectionStatus = document.querySelector("#connectionStatus");
const refreshButton = document.querySelector("#refreshButton");
const statusCards = document.querySelector("#statusCards");
const workloadList = document.querySelector("#workloadList");
const traceList = document.querySelector("#traceList");
const auditList = document.querySelector("#auditList");
const chatForm = document.querySelector("#chatForm");
const chatInput = document.querySelector("#chatInput");
const chatLog = document.querySelector("#chatLog");
const diagnosisForm = document.querySelector("#diagnosisForm");
const namespaceInput = document.querySelector("#namespaceInput");
const deploymentInput = document.querySelector("#deploymentInput");
const diagnosisOutput = document.querySelector("#diagnosisOutput");
const incidentMarkdown = document.querySelector("#incidentMarkdown");
const copyMarkdownButton = document.querySelector("#copyMarkdownButton");

function setConnectionStatus(message, state = "") {
  connectionStatus.textContent = message;
  connectionStatus.className = `connection-pill ${state}`.trim();
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
    const [status, health, traces, audit] = await Promise.all([
      apiFetch("/api/v1/status"),
      apiFetch("/api/v1/cluster/health"),
      apiFetch("/api/v1/traces?limit=6"),
      apiFetch("/api/v1/audit/events?limit=8"),
    ]);
    renderStatus(status);
    renderWorkloads(health);
    renderTraces(traces.spans || []);
    renderAuditEvents(audit.events || []);
    setConnectionStatus("API connected", "ok");
  } catch (error) {
    setConnectionStatus("API unavailable", "error");
    workloadList.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  } finally {
    refreshButton.disabled = false;
  }
}

function renderStatus(status) {
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
            ${workload.ready_replicas}/${workload.desired_replicas}
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
      (span) => `
        <div class="trace-row">
          <strong>${escapeHtml(span.name)}</strong>
          <span>${span.duration_ms.toFixed(2)} ms</span>
        </div>
      `,
    )
    .join("");
}

function renderAuditEvents(events) {
  if (!events.length) {
    auditList.innerHTML = `<div class="empty-state">Audit events will appear after API calls.</div>`;
    return;
  }
  auditList.innerHTML = events
    .map(
      (event) => `
        <div class="audit-row">
          <strong>${escapeHtml(event.method)} ${escapeHtml(event.path)}</strong>
          <span>${event.status_code}</span>
        </div>
      `,
    )
    .join("");
}

async function sendChat(message) {
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
    ? `<div class="source-list">${response.sources.map((source) => `<span>${escapeHtml(source)}</span>`).join("")}</div>`
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
  return `
    <div>${escapeHtml(response.answer)}</div>
    ${sources}
    ${citations}
  `;
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
  const submitButton = diagnosisForm.querySelector("button[type='submit']");
  submitButton.disabled = true;
  diagnosisOutput.innerHTML = `<div class="empty-state">Collecting pods, events, and logs...</div>`;
  incidentMarkdown.textContent = "Generating markdown report...";
  try {
    const encodedNamespace = encodeURIComponent(namespace);
    const encodedDeployment = encodeURIComponent(deployment);
    const [diagnosis, markdown] = await Promise.all([
      apiFetch(
        `/api/v1/cluster/namespaces/${encodedNamespace}/deployments/${encodedDeployment}/diagnose`,
      ),
      apiFetch(
        `/api/v1/cluster/namespaces/${encodedNamespace}/deployments/${encodedDeployment}/incident-report.md`,
      ),
    ]);
    renderDiagnosis(diagnosis);
    incidentMarkdown.textContent = markdown;
    await loadOverview();
  } catch (error) {
    diagnosisOutput.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    incidentMarkdown.textContent = "Incident report unavailable.";
  } finally {
    submitButton.disabled = false;
  }
}

function renderDiagnosis(diagnosis) {
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
  `;
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (character) => {
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
  refreshButton.addEventListener("click", () => {
    loadOverview();
  });
  workloadList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-namespace][data-deployment]");
    if (!button) {
      return;
    }
    namespaceInput.value = button.dataset.namespace;
    deploymentInput.value = button.dataset.deployment;
    diagnoseDeployment(button.dataset.namespace, button.dataset.deployment);
    document.querySelector("#diagnosis").scrollIntoView({ behavior: "smooth" });
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
      copyMarkdownButton.textContent = "Copied";
      setTimeout(() => {
        copyMarkdownButton.textContent = "Copy";
      }, 1600);
    } catch {
      copyMarkdownButton.textContent = "Copy failed";
    }
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
  diagnoseDeployment(namespaceInput.value.trim(), deploymentInput.value.trim());
}

boot();
