let baseUrl = "";
let pollInterval = null;

const UI = {
  screens: {
    connect: document.getElementById("connect-screen"),
    dashboard: document.getElementById("dashboard-screen")
  },
  inputs: {
    ip: document.getElementById("ip-input")
  },
  buttons: {
    connect: document.getElementById("btn-connect"),
    disconnect: document.getElementById("btn-disconnect"),
    launch: document.getElementById("btn-launch"),
    queue: document.getElementById("btn-queue")
  },
  display: {
    error: document.getElementById("connect-error"),
    phase: document.getElementById("phase-display"),
    queueMode: document.getElementById("queue-mode-display"),
    autoToggle: document.getElementById("auto-toggle"),
    statusIcon: document.getElementById("connection-status")
  }
};

// Auto-focus logic
window.addEventListener('DOMContentLoaded', () => {
    // Check if we saved an IP previously
    const savedIp = localStorage.getItem("leagueloop_ip");
    if (savedIp) {
        UI.inputs.ip.value = savedIp;
    }
});

// App Logic
UI.buttons.connect.addEventListener("click", async () => {
  const ip = UI.inputs.ip.value.trim() || "127.0.0.1";
  baseUrl = `http://${ip}:8337`;
  
  // Test connection
  try {
    const res = await fetch(`${baseUrl}/status`, { timeout: 3000 });
    if (res.ok) {
      localStorage.setItem("leagueloop_ip", ip);
      UI.display.error.classList.add("hidden");
      switchScreen("dashboard");
      startPolling();
    } else {
      throw new Error("HTTP Error");
    }
  } catch (err) {
    UI.display.error.classList.remove("hidden");
  }
});

UI.buttons.disconnect.addEventListener("click", () => {
  stopPolling();
  switchScreen("connect");
});

// Commands
async function sendAction(actionStr) {
  try {
    await fetch(`${baseUrl}/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: actionStr })
    });
  } catch (err) {
    console.error("Action failed", err);
  }
}

UI.buttons.launch.addEventListener("click", () => sendAction("launch_client"));
UI.buttons.queue.addEventListener("click", () => sendAction("find_match"));

// Checkbox doesn't use 'click', it listens to 'change'
// We intercept changes to toggle automation
UI.display.autoToggle.addEventListener("change", (e) => {
    // We send toggle immediately
    sendAction("toggle_automation");
    // Visually it switches immediately for responsiveness, polling will sync it
});

function switchScreen(name) {
  Object.values(UI.screens).forEach(s => s.classList.add("hidden"));
  UI.screens[name].classList.remove("hidden");
}

function startPolling() {
  if (pollInterval) clearInterval(pollInterval);
  fetchStatus(); // immediate
  pollInterval = setInterval(fetchStatus, 2000);
}

function stopPolling() {
  if (pollInterval) clearInterval(pollInterval);
}

async function fetchStatus() {
  try {
    const res = await fetch(`${baseUrl}/status`);
    if (!res.ok) throw new Error("Status failed");
    
    const data = await res.json();
    
    // Update dashboard UI
    UI.display.phase.innerText = formatPhase(data.phase || "None");
    UI.display.queueMode.innerText = `Mode: ${data.queue_mode || "Unknown"}`;
    
    // Only update toggle if it's vastly different to avoid jumpy UI while user clicks
    if (UI.display.autoToggle.checked !== data.automation_enabled) {
      UI.display.autoToggle.checked = data.automation_enabled;
    }

    UI.display.statusIcon.style.color = "var(--success)";
    UI.display.statusIcon.innerText = "● Connected";

  } catch (err) {
    UI.display.phase.innerText = "Disconnected";
    UI.display.statusIcon.style.color = "var(--error)";
    UI.display.statusIcon.innerText = "● Offline";
  }
}

function formatPhase(phase) {
  const map = {
    "None": "Idle",
    "Lobby": "In Lobby",
    "Matchmaking": "In Queue...",
    "ReadyCheck": "Match Found!",
    "ChampSelect": "Champ Select",
    "InProgress": "In Game"
  };
  return map[phase] || phase;
}
