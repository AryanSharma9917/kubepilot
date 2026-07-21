const API_BASE = "";

const connectionStatus = document.querySelector("#connectionStatus");
const statusCards = document.querySelector("#statusCards");
const workloadList = document.querySelector("#workloadList");
const traceList = document.querySelector("#traceList");

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
  loadOverview();
}

boot();
