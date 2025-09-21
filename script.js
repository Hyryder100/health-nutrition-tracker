(() => {
  const messagesEl = document.getElementById('messages');
  const formEl = document.getElementById('composer');
  const inputEl = document.getElementById('input');
  const sendBtn = document.getElementById('sendBtn');
  const clearBtn = document.getElementById('clearBtn');
  const crisisBtn = document.getElementById('crisisBtn');
  const quickReplyEls = Array.from(document.querySelectorAll('.quick-replies .chip'));
  const crisisModal = document.getElementById('crisisModal');
  const closeCrisis = document.getElementById('closeCrisis');
  const okCrisis = document.getElementById('okCrisis');
  const toggleBreath = document.getElementById('toggleBreath');
  const breathCircle = document.querySelector('.breath-circle');
  const breathPhase = document.querySelector('.breath .phase');

  const STORAGE_KEY = 'calm_companion_history_v1';

  const supportiveReplies = {
    onboarding: [
      "Hi, I’m here to listen. How are you feeling today?",
    ],
    overwhelmed: [
      "I'm sorry it feels like a lot right now. Let’s take one small step together. What’s one thing you can put down or delay today?",
      "Your feelings are valid. It’s okay to pause. Try placing a hand on your chest and taking 3 slow breaths with me.",
    ],
    encouragement: [
      "You’ve made it through hard days before. I’m proud of you for reaching out.",
      "Progress isn’t linear, and that’s okay. Small steps still count.",
    ],
    coping: [
      "Coping idea: 4-4-6 breathing. Inhale 4s, hold 4s, exhale 6s. Repeat 5 times.",
      "Coping idea: Grounding. Look for 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, 1 you can taste.",
    ],
    general: [
      "Thank you for sharing that. I’m here with you. What would feel supportive right now?",
      "That sounds tough. Would you like encouragement, a coping strategy, or just space to vent?",
    ],
  };

  const keywordMap = [
    { keys: ["overwhelmed", "too much", "stressed", "anxious"], tag: "overwhelmed" },
    { keys: ["encourage", "motivation", "hope", "support"], tag: "encouragement" },
    { keys: ["cope", "coping", "strategy", "tip", "help"], tag: "coping" },
    { keys: ["panic", "crisis", "emergency"], tag: "crisis" },
  ];

  function saveHistory(history) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch {}
  }

  function loadHistory() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch { return []; }
  }

  function clearHistory() {
    try { localStorage.removeItem(STORAGE_KEY); } catch {}
  }

  function formatTime(date) {
    return new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' }).format(date);
  }

  function createMessageElement(role, text, time) {
    const wrapper = document.createElement('div');
    wrapper.className = `msg ${role}`;

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;

    const timeEl = document.createElement('span');
    timeEl.className = 'time';
    timeEl.textContent = formatTime(new Date(time));

    if (role === 'user') {
      wrapper.appendChild(timeEl);
      wrapper.appendChild(bubble);
    } else {
      wrapper.appendChild(bubble);
      wrapper.appendChild(timeEl);
    }
    return wrapper;
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function pickRandom(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

  function classify(text) {
    const lower = text.toLowerCase();
    for (const group of keywordMap) {
      if (group.keys.some(k => lower.includes(k))) return group.tag;
    }
    return 'general';
  }

  async function generateBotReply(userText) {
    // Try backend API first; fall back to local logic
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 2500);
      const res = await fetch('/api/reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: userText }),
        signal: controller.signal,
      });
      clearTimeout(timeout);
      if (res.ok) {
        const data = await res.json();
        if (data && typeof data.reply === 'string') return data.reply;
      }
      // non-OK fallthrough to local
    } catch {}

    const tag = classify(userText);
    if (tag === 'crisis') {
      return "It sounds urgent. I care about your safety. If you might harm yourself or others, please contact local emergency services or use the Crisis Support button for immediate help.";
    }
    const options = supportiveReplies[tag] || supportiveReplies.general;
    return pickRandom(options);
  }

  function loadInitialMessages() {
    const history = loadHistory();
    if (history.length === 0) {
      const now = Date.now();
      const intro = supportiveReplies.onboarding[0];
      const msg = { role: 'bot', text: intro, time: now };
      renderMessage(msg);
      saveHistory([msg]);
      return;
    }
    for (const item of history) renderMessage(item);
  }

  function renderMessage(message) {
    const el = createMessageElement(message.role, message.text, message.time);
    messagesEl.appendChild(el);
    scrollToBottom();
  }

  function appendAndPersist(role, text) {
    const message = { role, text, time: Date.now() };
    renderMessage(message);
    const history = loadHistory();
    history.push(message);
    saveHistory(history);
  }

  function handleSend(text) {
    const trimmed = text.trim();
    if (!trimmed) return;
    appendAndPersist('user', trimmed);
    inputEl.value = '';
    autoResize();

    sendBtn.disabled = true;
    setTimeout(async () => {
      const reply = await generateBotReply(trimmed);
      appendAndPersist('bot', reply);
      sendBtn.disabled = false;
      inputEl.focus();
    }, 450 + Math.random() * 600);
  }

  function autoResize() {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + 'px';
  }

  // Crisis modal controls
  function openCrisis() {
    crisisModal.hidden = false;
    crisisModal.querySelector('.modal-card').focus?.();
    startBreathLoop();
  }
  function closeCrisisModal() {
    crisisModal.hidden = true;
    stopBreathLoop();
    crisisBtn.focus();
  }
  crisisBtn.addEventListener('click', openCrisis);
  closeCrisis.addEventListener('click', closeCrisisModal);
  okCrisis.addEventListener('click', closeCrisisModal);
  crisisModal.addEventListener('click', (e) => {
    if (e.target instanceof HTMLElement && e.target.dataset.close === 'true') closeCrisisModal();
  });

  // Breathing phase text loop synchronized with CSS timing (14s total)
  let breathTimer = null;
  let breathRunning = true;
  function setPhaseText() {
    if (!breathPhase) return;
    breathPhase.textContent = 'Inhale';
    setTimeout(() => { if (breathPhase && breathRunning) breathPhase.textContent = 'Hold'; }, 2800);
    setTimeout(() => { if (breathPhase && breathRunning) breathPhase.textContent = 'Exhale'; }, 7000);
  }
  function startBreathLoop() {
    breathRunning = true;
    breathCircle && (breathCircle.style.animationPlayState = 'running');
    setPhaseText();
    breathTimer = setInterval(setPhaseText, 14000);
    toggleBreath.setAttribute('aria-pressed', 'false');
    toggleBreath.textContent = 'Pause';
  }
  function stopBreathLoop() {
    breathRunning = false;
    breathCircle && (breathCircle.style.animationPlayState = 'paused');
    if (breathTimer) { clearInterval(breathTimer); breathTimer = null; }
  }
  toggleBreath.addEventListener('click', () => {
    if (breathRunning) {
      stopBreathLoop();
      toggleBreath.setAttribute('aria-pressed', 'true');
      toggleBreath.textContent = 'Resume';
    } else {
      startBreathLoop();
    }
  });

  // Input handlers
  formEl.addEventListener('submit', (e) => {
    e.preventDefault();
    handleSend(inputEl.value);
  });
  inputEl.addEventListener('input', autoResize);
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(inputEl.value);
    }
  });
  clearBtn.addEventListener('click', () => {
    messagesEl.innerHTML = '';
    clearHistory();
    loadInitialMessages();
  });

  // Quick replies
  quickReplyEls.forEach(btn => {
    btn.addEventListener('click', () => {
      handleSend(btn.dataset.text || btn.textContent || '');
    });
  });

  // Accessibility: ensure region announces new content
  messagesEl.setAttribute('aria-live', matchMedia('(prefers-reduced-motion: reduce)').matches ? 'polite' : 'polite');

  // Initial render
  loadInitialMessages();
  autoResize();
})();

