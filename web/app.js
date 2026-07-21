const API_BASE = "";

const connectionStatus = document.querySelector("#connectionStatus");
const statusCards = document.querySelector("#statusCards");
const workloadList = document.querySelector("#workloadList");
const traceList = document.querySelector("#traceList");
const chatForm = document.querySelector("#chatForm");
const chatInput = document.querySelector("#chatInput");
const chatLog = document.querySelector("#chatLog");

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
  try {
    const [status, health, traces] = await Promise.all([
      apiFetch("/api/v1/status"),
      apiFetch("/api/v1/cluster/health"),
      apiFetch("/api/v1/traces?limit=6"),
    ]);
    renderStatus(status);
    renderWorkloads(health);
    renderTraces(traces.spans || []);
    setConnectionStatus("API connected", "ok");
  } catch (error) {
    setConnectionStatus("API unavailable", "error");
    workloadList.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
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
          <b>${workload.ready_replicas}/${workload.desired_replicas}</b>
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

async function sendChat(message) {
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
  chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const message = chatInput.value.trim();
    if (!message) {
      return;
    }
    chatInput.value = "";
    sendChat(message);
  });
  loadOverview();
}

boot();
