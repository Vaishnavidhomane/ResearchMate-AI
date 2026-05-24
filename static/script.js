/* ── Tab switching ─────────────────────────────────────────── */
function switchTab(tabId) {
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach(p => {
    p.hidden = true;
    p.style.display = "";
  });

  const pane = document.getElementById(`tab-${tabId}`);
  const btn  = document.querySelector(`.tab[data-tab="${tabId}"]`);
  if (pane) { pane.hidden = false; if (tabId === "chat") pane.style.display = "flex"; }
  if (btn)  btn.classList.add("active");
}

document.querySelectorAll(".tab").forEach(btn => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});


/* ══════════════════════════════════════════════════════════════
   QUIZ ENGINE
══════════════════════════════════════════════════════════════ */
let qIdx   = 0;
let score  = 0;
let log    = [];   // {chosen, correct} per question
const quiz = PAPER.quiz;

function renderQuestion() {
  const q   = quiz[qIdx];
  const pct = (qIdx / quiz.length) * 100;

  document.getElementById("q-counter").textContent  = `Question ${qIdx + 1} of ${quiz.length}`;
  document.getElementById("q-score").textContent    = `Score ${score} / ${quiz.length}`;
  document.getElementById("q-progress").style.width = pct + "%";
  document.getElementById("q-text").textContent     = q.question;
  document.getElementById("q-explanation").hidden   = true;
  document.getElementById("q-next").hidden          = true;

  const optContainer = document.getElementById("q-options");
  optContainer.innerHTML = "";
  q.options.forEach((opt, i) => {
    const btn = document.createElement("button");
    btn.className = "quiz-opt";
    btn.innerHTML = `<span class="opt-letter">${String.fromCharCode(65 + i)})</span>${opt}`;
    btn.addEventListener("click", () => pickAnswer(i));
    optContainer.appendChild(btn);
  });
}

function pickAnswer(chosen) {
  const q       = quiz[qIdx];
  const correct = chosen === q.answer;
  if (correct) score++;
  log.push({ chosen, correct });

  // Style buttons
  document.querySelectorAll(".quiz-opt").forEach((btn, i) => {
    btn.classList.add("disabled");
    btn.disabled = true;
    if (i === q.answer)  btn.classList.add("correct");
    else if (i === chosen) btn.classList.add("wrong");
  });

  // Show explanation
  const exBox = document.getElementById("q-explanation");
  exBox.innerHTML = `<strong>💡 Explanation: </strong>${q.explanation}`;
  exBox.hidden = false;

  // Update score display immediately
  document.getElementById("q-score").textContent = `Score ${score} / ${quiz.length}`;

  // Show next/finish button
  const nextBtn = document.getElementById("q-next");
  nextBtn.textContent = (qIdx + 1 >= quiz.length) ? "See Results →" : "Next Question →";
  nextBtn.hidden = false;
}

function nextQuestion() {
  if (qIdx + 1 >= quiz.length) {
    showResults();
  } else {
    qIdx++;
    renderQuestion();
  }
}

function showResults() {
  document.getElementById("quiz-main").hidden    = true;
  document.getElementById("quiz-results").hidden = false;

  const emoji = score === quiz.length ? "🏆" : score >= Math.ceil(quiz.length * 0.6) ? "🎯" : "📚";
  const msg   = score === quiz.length
    ? "Perfect! You've truly understood this paper."
    : score >= Math.ceil(quiz.length * 0.6)
    ? "Good grasp of the material!"
    : "Review the summary and try again.";

  document.getElementById("result-emoji").textContent = emoji;
  document.getElementById("result-score").textContent = `${score} / ${quiz.length}`;
  document.getElementById("result-msg").textContent   = msg;

  // Review cards
  const review = document.getElementById("result-review");
  review.innerHTML = "";
  quiz.forEach((q, i) => {
    const entry = log[i] || {};
    const card  = document.createElement("div");
    card.className = "result-card";
    card.style.borderLeft = `3px solid ${entry.correct ? "var(--green)" : "var(--red)"}`;

    let html = `<div class="rq">Q${i + 1}: ${q.question}</div>`;
    html += `<div class="ra" style="color:${entry.correct ? "var(--green)" : "var(--red)"}">
      Your answer: ${q.options[entry.chosen] || "—"} ${entry.correct ? "✓" : "✗"}
    </div>`;
    if (!entry.correct) {
      html += `<div class="ra" style="color:var(--green)">Correct: ${q.options[q.answer]}</div>`;
    }
    html += `<div class="re">${q.explanation}</div>`;

    card.innerHTML = html;
    review.appendChild(card);
  });
}

function resetQuiz() {
  qIdx  = 0;
  score = 0;
  log   = [];
  document.getElementById("quiz-main").hidden    = false;
  document.getElementById("quiz-results").hidden = true;
  renderQuestion();
}

// Init quiz on page load
renderQuestion();


/* ══════════════════════════════════════════════════════════════
   CHAT Q&A
══════════════════════════════════════════════════════════════ */
let chatHistory = [];   // [{role, content}]

function setInput(text) {
  const input = document.getElementById("chat-input");
  input.value = text;
  input.focus();
}

function addBubble(role, text) {
  const empty = document.querySelector(".chat-empty");
  if (empty) empty.remove();

  const messages = document.getElementById("chat-messages");
  const wrap     = document.createElement("div");
  wrap.className = `chat-bubble ${role}`;

  const inner    = document.createElement("div");
  inner.className = "bubble-inner";
  inner.textContent = text;

  wrap.appendChild(inner);
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
  return inner;
}

function addTypingIndicator() {
  const empty = document.querySelector(".chat-empty");
  if (empty) empty.remove();

  const messages = document.getElementById("chat-messages");
  const wrap     = document.createElement("div");
  wrap.className = "chat-bubble bot";
  wrap.id        = "typing-indicator";

  const inner    = document.createElement("div");
  inner.className = "bubble-inner";
  inner.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';

  wrap.appendChild(inner);
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
}

function removeTypingIndicator() {
  const el = document.getElementById("typing-indicator");
  if (el) el.remove();
}

async function sendChat() {
  const input = document.getElementById("chat-input");
  const question = input.value.trim();
  if (!question) return;

  input.value = "";
  addBubble("user", question);
  addTypingIndicator();

  // Disable input while waiting
  input.disabled = true;

  try {
    const res  = await fetch("/chat", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        paper_id: PAPER.paper_id,
        question,
        history: chatHistory.slice(-6),   // send last 3 exchanges
      }),
    });

    const data = await res.json();
    removeTypingIndicator();

    if (!res.ok || data.error) {
      addBubble("bot", "⚠️ " + (data.error || "Something went wrong. Please try again."));
    } else {
      addBubble("bot", data.answer);
      // Update history
      chatHistory.push({ role: "user",      content: question     });
      chatHistory.push({ role: "assistant", content: data.answer  });
    }
  } catch (err) {
    removeTypingIndicator();
    addBubble("bot", "⚠️ Network error: " + err.message);
  }

  input.disabled = false;
  input.focus();
}
