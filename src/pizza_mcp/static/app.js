const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const send = document.querySelector("#send");
const messages = document.querySelector("#messages");
const status = document.querySelector("#status");
let conversationId = sessionStorage.getItem("pizza-conversation");

function appendMessage(text, role) {
  const row = document.createElement("div");
  row.className = `message ${role}`;
  if (role === "assistant") {
    const avatar = document.createElement("span");
    avatar.className = "message-avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = "✳";
    row.append(avatar);
  }
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  row.append(bubble);
  messages.append(row);
  messages.scrollTop = messages.scrollHeight;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message || send.disabled) return;
  send.disabled = true;
  input.disabled = true;
  status.textContent = "Asistent přemýšlí…";
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Zprávu se nepodařilo odeslat.");
    appendMessage(message, "user");
    appendMessage(data.answer, "assistant");
    conversationId = data.conversation_id;
    sessionStorage.setItem("pizza-conversation", conversationId);
    input.value = "";
    status.textContent = "";
  } catch (error) {
    status.textContent = error.message;
  } finally {
    send.disabled = false;
    input.disabled = false;
    input.focus();
  }
});

document.querySelector("#reset").addEventListener("click", () => {
  conversationId = null;
  sessionStorage.removeItem("pizza-conversation");
  messages.replaceChildren();
  appendMessage("Ahoj! 👋 Vítej u Pizzy na Pankráci. Na co máš dnes chuť?", "assistant");
  status.textContent = "";
  input.focus();
});

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.textContent;
    input.focus();
  });
});
