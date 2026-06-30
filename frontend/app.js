/* ==========================================================================
   University Student Support Assistant - app.js
   Talks to the FastAPI backend (/health and /ask) and manages all UI
   states: normal reply, empty question, backend down, model error,
   and slow response (loading indicator).
   ========================================================================== */

// Change this if your backend runs on a different host/port.
const API_BASE_URL = "http://localhost:8000";

const conversation = document.getElementById("conversation");
const composerForm = document.getElementById("composerForm");
const questionInput = document.getElementById("questionInput");
const sendButton = document.getElementById("sendButton");
const sendButtonLabel = document.getElementById("sendButtonLabel");
const inputHint = document.getElementById("inputHint");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const connectionBanner = document.getElementById("connectionBanner");
const connectionBannerText = document.getElementById("connectionBannerText");
const topicList = document.getElementById("topicList");

let backendOnline = false;

/* ---------------------------------------------------------- helpers --- */

function addBubble({ role, text, faqTag = null, meta = null }) {
  const bubble = document.createElement("div");
  bubble.className = `bubble bubble-${role}`;

  const label = document.createElement("div");
  label.className = "bubble-label";

  const roleSpan = document.createElement("span");
  roleSpan.textContent = role === "user" ? "You" : role === "error" ? "System" : "Assistant";
  label.appendChild(roleSpan);

  if (faqTag) {
    const tag = document.createElement("span");
    tag.className = "faq-tag";
    tag.textContent = `FAQ match: ${faqTag}`;
    label.appendChild(tag);
  }

  const textEl = document.createElement("div");
  textEl.className = "bubble-text";
  textEl.textContent = text;

  bubble.appendChild(label);
  bubble.appendChild(textEl);

  if (meta) {
    const metaEl = document.createElement("div");
    metaEl.className = "bubble-meta";
    metaEl.textContent = meta;
    bubble.appendChild(metaEl);
  }

  conversation.appendChild(bubble);
  conversation.scrollTop = conversation.scrollHeight;
  return bubble;
}

function addLoadingBubble() {
  const bubble = document.createElement("div");
  bubble.className = "bubble bubble-assistant";
  bubble.id = "loadingBubble";
  bubble.innerHTML = `
    <div class="bubble-label"><span>Assistant</span></div>
    <div class="bubble-text">
      <span class="typing"><span></span><span></span><span></span></span>
      &nbsp;thinking&hellip;
    </div>
  `;
  conversation.appendChild(bubble);
  conversation.scrollTop = conversation.scrollHeight;
  return bubble;
}

function removeLoadingBubble() {
  const el = document.getElementById("loadingBubble");
  if (el) el.remove();
}

function setBackendStatus(online, label) {
  backendOnline = online;
  statusDot.classList.toggle("online", online);
  statusDot.classList.toggle("offline", !online);
  statusText.textContent = label;
}

function showConnectionBanner(message) {
  connectionBannerText.textContent = message;
  connectionBanner.hidden = false;
}

function hideConnectionBanner() {
  connectionBanner.hidden = true;
}

function setSending(isSending) {
  sendButton.disabled = isSending;
  sendButtonLabel.textContent = isSending ? "Sending…" : "Ask";
  questionInput.disabled = isSending;
}

/* ---------------------------------------------------- health check --- */

async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, { method: "GET" });
    if (!response.ok) throw new Error("Backend responded with an error.");
    const data = await response.json();
    setBackendStatus(true, `online · model: ${data.model || "unknown"}`);
    hideConnectionBanner();
  } catch (err) {
    // Situation: "Backend is not running" -> frontend shows connection error.
    setBackendStatus(false, "backend offline");
    showConnectionBanner(
      "Could not reach the backend server. Make sure it is running (uvicorn backend.main:app --reload) " +
      "and try again."
    );
  }
}

/* -------------------------------------------------------- submit Q&A -- */

async function handleAsk(question) {
  hideConnectionBanner();
  setSending(true);
  const loadingBubble = addLoadingBubble();

  // "Slow response" handling: after 4s, tweak the loading text so the
  // student knows the assistant is still working on a slower model.
  const slowTimer = setTimeout(() => {
    const el = loadingBubble.querySelector(".bubble-text");
    if (el) {
      el.innerHTML = `
        <span class="typing"><span></span><span></span><span></span></span>
        &nbsp;still thinking, local models can take a moment&hellip;
      `;
    }
  }, 4000);

  try {
    const response = await fetch(`${API_BASE_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    clearTimeout(slowTimer);
    removeLoadingBubble();

    if (!response.ok) {
      // Situation: "model is not running" -> backend returns 502/503 with detail.
      const errorBody = await response.json().catch(() => ({}));
      const detail = errorBody.detail || `Request failed with status ${response.status}.`;
      addBubble({ role: "error", text: detail });
      return;
    }

    const data = await response.json();
    addBubble({
      role: "assistant",
      text: data.answer,
      faqTag: data.faq_topic,
      meta: `answered in ${data.response_time_seconds}s`,
    });
  } catch (err) {
    clearTimeout(slowTimer);
    removeLoadingBubble();
    // Network-level failure mid-conversation (backend went down, etc.)
    addBubble({
      role: "error",
      text: "Connection lost while waiting for a reply. Check that the backend is still running.",
    });
    setBackendStatus(false, "backend offline");
    showConnectionBanner("Lost connection to the backend server.");
  } finally {
    setSending(false);
    questionInput.focus();
  }
}

/* ----------------------------------------------------------- events --- */

composerForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();

  // Situation: "Empty question" -> frontend asks user to enter a question.
  if (!question) {
    inputHint.textContent = "Please enter a question before sending.";
    questionInput.focus();
    return;
  }
  inputHint.textContent = "";

  addBubble({ role: "user", text: question });
  questionInput.value = "";
  autoGrow();
  handleAsk(question);
});

questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    composerForm.requestSubmit();
  }
});

questionInput.addEventListener("input", () => {
  if (questionInput.value.trim()) inputHint.textContent = "";
  autoGrow();
});

function autoGrow() {
  questionInput.style.height = "auto";
  questionInput.style.height = `${Math.min(questionInput.scrollHeight, 140)}px`;
}

topicList.addEventListener("click", (event) => {
  const li = event.target.closest("li[data-q]");
  if (!li) return;
  questionInput.value = li.dataset.q;
  inputHint.textContent = "";
  autoGrow();
  questionInput.focus();
});

/* ----------------------------------------------------------- startup -- */

checkBackendHealth();
setInterval(checkBackendHealth, 15000); // keep status indicator fresh
