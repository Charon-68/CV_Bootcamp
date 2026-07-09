/**
 * NexusGuard Frontend
 * Connects to WebSockets and displays live incidents.
 */

const API_BASE = (window.NexusGuard_API_BASE || "http://localhost:8000").replace(/\/$/, "");
const WS_BASE = API_BASE.replace(/^http/, "ws");

const els = {
  backend: () => document.getElementById("backend"),
  analyzeBtn: () => document.getElementById("analyze"),
  payload: () => document.getElementById("payload"),
  timeline: () => document.getElementById("timeline"),
  metFps: () => document.getElementById("met-fps"),
  metIncidents: () => document.getElementById("met-incidents")
};

let incidentCount = 0;
let framesProcessed = 0;
let startTime = Date.now();

function getRiskClass(risk) {
  if (risk >= 0.7) return "high-risk";
  if (risk >= 0.3) return "medium-risk";
  return "low-risk";
}

function appendEvent(event) {
  const tl = els.timeline();
  if (incidentCount === 0) {
    tl.innerHTML = "";
  }
  
  incidentCount++;
  els.metIncidents().innerText = incidentCount;

  const div = document.createElement("div");
  div.className = `event ${getRiskClass(event.risk)}`;
  const time = new Date().toLocaleTimeString();
  div.innerHTML = `<strong>[${time}] Frame ${event.frame_index}</strong> - Risk: ${(event.risk * 100).toFixed(0)}%<br/>
                   <em>${event.label}</em>: ${event.summary}`;
  
  tl.prepend(div);
  
  // Keep only last 50 events
  if (tl.children.length > 50) {
    tl.removeChild(tl.lastChild);
  }
}

function updateFPS() {
  const elapsed = (Date.now() - startTime) / 1000;
  if (elapsed > 0) {
    els.metFps().innerText = (framesProcessed / elapsed).toFixed(1);
  }
}

function initWebSocket() {
  const ws = new WebSocket(`${WS_BASE}/v1/ws`);
  
  ws.onopen = () => {
    els.backend().textContent = "Status: Connected (Live)";
    els.backend().style.background = "#00cc66";
  };
  
  ws.onmessage = (msg) => {
    try {
      const data = JSON.parse(msg.data);
      appendEvent(data);
    } catch (e) {
      console.error("Failed to parse event", e);
    }
  };
  
  ws.onclose = () => {
    els.backend().textContent = "Status: Disconnected";
    els.backend().style.background = "#ff4444";
    setTimeout(initWebSocket, 3000); // Reconnect
  };
}

async function analyzeFrame() {
  const btn = els.analyzeBtn();
  btn.disabled = true;
  btn.innerText = "Analyzing...";
  
  try {
    const payload = JSON.parse(els.payload().value);
    const res = await fetch(`${API_BASE}/v1/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (res.ok) {
      framesProcessed++;
      updateFPS();
    }
  } catch (err) {
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.innerText = "Analyze Frame";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initWebSocket();
  els.analyzeBtn().addEventListener("click", analyzeFrame);
  
  // Simulate FPS processing rate update
  setInterval(updateFPS, 1000);
});
