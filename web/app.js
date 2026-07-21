const connectionStatus = document.querySelector("#connectionStatus");

function setConnectionStatus(message, state = "") {
  connectionStatus.textContent = message;
  connectionStatus.className = `connection-pill ${state}`.trim();
}

function boot() {
  setConnectionStatus("UI ready", "ok");
}

boot();
