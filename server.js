const path = require('path');
const express = require('express');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json({ limit: '64kb' }));

// Serve static frontend files
app.use(express.static(__dirname, { extensions: ['html'] }));

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Supportive reply logic (mirrors client)
const supportiveReplies = {
  onboarding: [
    'Hi, I’m here to listen. How are you feeling today?',
  ],
  overwhelmed: [
    "I'm sorry it feels like a lot right now. Let’s take one small step together. What’s one thing you can put down or delay today?",
    'Your feelings are valid. It’s okay to pause. Try placing a hand on your chest and taking 3 slow breaths with me.',
  ],
  encouragement: [
    'You’ve made it through hard days before. I’m proud of you for reaching out.',
    'Progress isn’t linear, and that’s okay. Small steps still count.',
  ],
  coping: [
    'Coping idea: 4-4-6 breathing. Inhale 4s, hold 4s, exhale 6s. Repeat 5 times.',
    'Coping idea: Grounding. Look for 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, 1 you can taste.',
  ],
  general: [
    'Thank you for sharing that. I’m here with you. What would feel supportive right now?',
    'That sounds tough. Would you like encouragement, a coping strategy, or just space to vent?',
  ],
};

const keywordMap = [
  { keys: ['overwhelmed', 'too much', 'stressed', 'anxious'], tag: 'overwhelmed' },
  { keys: ['encourage', 'motivation', 'hope', 'support'], tag: 'encouragement' },
  { keys: ['cope', 'coping', 'strategy', 'tip', 'help'], tag: 'coping' },
  { keys: ['panic', 'crisis', 'emergency'], tag: 'crisis' },
];

function classify(text) {
  const lower = String(text || '').toLowerCase();
  for (const group of keywordMap) {
    if (group.keys.some(k => lower.includes(k))) return group.tag;
  }
  return 'general';
}

function pickRandom(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

function generateBotReply(userText) {
  const tag = classify(userText);
  if (tag === 'crisis') {
    return {
      reply: 'It sounds urgent. I care about your safety. If you might harm yourself or others, please contact local emergency services or use the Crisis Support button for immediate help.',
      tag,
    };
  }
  const options = supportiveReplies[tag] || supportiveReplies.general;
  return { reply: pickRandom(options), tag };
}

// Reply API
app.post('/api/reply', (req, res) => {
  try {
    const text = (req.body && typeof req.body.text === 'string') ? req.body.text : '';
    const { reply, tag } = generateBotReply(text);
    res.json({ reply, tag });
  } catch (err) {
    res.status(500).json({ error: 'internal_error' });
  }
});

// Fallback to index.html for direct deep links (optional)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Calm Companion server running at http://localhost:${PORT}`);
});

