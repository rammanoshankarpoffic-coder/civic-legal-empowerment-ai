const API_BASE = "http://localhost:5000";
const SESSION_ID = "web-" + Math.random().toString(36).slice(2);

const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const modeIndicator = document.getElementById("mode-indicator");

function addBubble(text, sender, meta) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${sender}`;
  bubble.textContent = text;
  if (meta) {
    const metaEl = document.createElement("span");
    metaEl.className = "meta";
    metaEl.textContent = meta;
    bubble.appendChild(metaEl);
  }
  chatWindow.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage(message) {
  addBubble(message, "user");
  addBubble("Thinking...", "bot");
  const thinkingBubble = chatWindow.lastChild;

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: SESSION_ID, language: "en" }),
    });
    const data = await res.json();
    chatWindow.removeChild(thinkingBubble);

    const mainText =
      data.clarifying_question ||
      data.application_text ||
      data.explanation ||
      data.reasoning ||
      data.next_question ||
      data.rendered_document ||
      JSON.stringify(data, null, 2);

    const meta = `agent: ${data.agent || data.detected_intent || "unknown"}`;
    addBubble(mainText, "bot", meta);
  } catch (err) {
    chatWindow.removeChild(thinkingBubble);
    addBubble(
      "Could not reach the backend. Is it running on http://localhost:5000 ?",
      "bot"
    );
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;
  chatInput.value = "";
  sendMessage(message);
});

document.querySelectorAll(".quick-prompts button").forEach((btn) => {
  btn.addEventListener("click", () => sendMessage(btn.dataset.prompt));
});

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    const data = await res.json();
    modeIndicator.textContent = data.mode + (data.mode === "mock" ? " (no LLM provider configured)" : "");
  } catch {
    modeIndicator.textContent = "backend offline";
  }
}

checkHealth();
addBubble(
  "Hi! I'm Nyaya Sathi. Ask me about an RTI, a tenant/consumer/workplace dispute, a government scheme, or say you want to fill a form.",
  "bot"
);
