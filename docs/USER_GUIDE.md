# ETIB Interpreter Trainer — User Guide

**École de Traducteurs et d'Interprètes de Beyrouth, USJ Beirut**

This guide explains how to use the ETIB Interpreter Self-Training Platform. No technical knowledge is required.

**Live platform:** the link your instructor or teammate shared with you (Vercel-hosted).

---

## Table of contents

1. [Getting in — account or guest](#1-getting-in)
2. [First-time setup — get your API key](#2-first-time-setup)
3. [Module A — Generate a training speech](#3-module-a--generate-a-training-speech)
4. [Module B — Listen to the speech and get study materials](#4-module-b--listen-and-study)
5. [Module C — Record your interpretation](#5-module-c--record-your-interpretation)
6. [Module D — Get your evaluation](#6-module-d--get-your-evaluation)
7. [The chat assistant](#7-the-chat-assistant)
8. [Tips for effective practice](#8-tips-for-effective-practice)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Getting in

You have two options — no instructor approval needed for either:

**Option A — Continue as Guest (fastest)**
1. Open the platform link
2. Click **Continue as Guest** below the login form
3. You're in immediately — no email, no password

**Option B — Create an account** (keeps your history saved across visits/devices)
1. Click **Create an account**
2. Enter your full name, email, and a password (at least 8 characters)
3. Click **Create account** — you are logged in automatically
4. Next time, use **Sign in** with your email and password

> Guest mode does not save your evaluation history between browser sessions. Create an account if you want to track progress over time.

---

## 2. First-time setup — get your API key

The platform uses **Groq** to generate speeches, transcribe audio, and evaluate your performance. Groq is free — every user needs their own personal key (the platform does not provide a shared one).

### Step 1 — Create a free Groq account
1. Go to **[console.groq.com](https://console.groq.com)**
2. Sign up with your email (free, no credit card)
3. Go to **API Keys** in the left menu
4. Click **Create API key**, name it (e.g. "ETIB"), and copy it — it starts with `gsk_`

> Keep your key private. If it leaks, delete it on console.groq.com and create a new one.

### Step 2 — Add your key to the platform
1. Click the **⚙** gear icon in the top navigation bar — opens Settings
2. Paste your key (starts with `gsk_`)
3. Click **Test key** — you should see "Key is valid"
4. Click **Save key**

Your key is saved in your browser only (localStorage) — no one else can see it, and it stays saved across visits unless you clear your browser data.

> If you don't add a key, you'll see a yellow banner reminding you — speech generation, transcription, and evaluation all require it.

---

## 3. Module A — Generate a training speech

1. Click **Generate speech** in the navigation bar
2. Choose the **Speech language** (the language the speaker uses: AR, FR, or EN)
3. Choose the **Target language** (the language you will interpret into)
4. Type any **Topic** — completely free text, e.g. "AI in education", "nuclear disarmament", "water scarcity in Lebanon"
5. Choose a **Domain** from 12 options: Politics, Diplomacy, Economics, Health, Education, Climate & Environment, Human Rights, Technology & AI, Migration & Refugees, Disarmament, Women & Gender, Food & Hunger
6. Adjust difficulty (Beginner/Intermediate/Advanced) and click **⚙ More** for additional settings: word count, structure, scenario, pressure simulation (speed, topic shifts, cognitive load)
7. Click **Generate speech**

### Document-grounded generation
Upload a PDF or Word file as source material — the AI extracts the key content and builds the speech around it.

### UN Library
Search real United Nations documents by topic/domain and use one as your speech's grounding source for factual accuracy.

---

## 4. Module B — Listen and study

After generating a speech, click **Audio & materials**.

1. Choose a **voice accent** (Lebanese/Gulf/Egyptian Arabic, Parisian/Canadian French, US/UK/AU English)
2. Adjust **speech rate** if needed
3. Click **Generate audio** — listen as if you were in a booth
4. Click **Generate materials** for key terms, a thematic summary, MCQs, and a trilingual glossary
5. **Download glossary (DOCX)** to study offline

---

## 5. Module C — Record your interpretation

1. Click **Record & transcribe**
2. Click the record button and interpret the speech
3. Click **Stop**, then **Transcribe**
4. Your transcript appears with timestamps; low-confidence words are highlighted (possible pronunciation issues)

---

## 6. Module D — Get your evaluation

Click **Evaluation**. This compares your interpretation against the original speech.

**What you get:**
- **Overall score, coverage score, fluency score** (0–10)
- **Translation errors** — specific wrong renderings, with the correct equivalent
- **Missing content** — ideas you didn't cover
- **Number accuracy** — every figure/date/statistic checked individually
- **Hesitations, repetitions, long pauses** — detected automatically and commented on
- **Pronunciation flags** — words the AI was uncertain about, with likely correction
- **Strengths and recommendations** — specific, actionable next steps

> The evaluator is calibrated to be strict, like a real professor — it will flag genuine errors rather than give the benefit of the doubt. A 5–7/10 on a first attempt is normal; focus on consistency across sessions, not a single high score.

---

## 7. The chat assistant

Click the **💬** button in the bottom-right corner on any screen. Ask it about interpretation technique (consecutive vs. simultaneous, note-taking systems, how to reduce hesitations), terminology, or how to use any module. It answers in whatever language you write in.

---

## 8. Tips for effective practice

- Use **Advanced** difficulty once you consistently score above 7/10 on Intermediate
- Turn on hesitations/pressure settings to simulate real speaker conditions
- Study the **key terms and glossary** before recording — reduces cognitive load
- Practice daily for 20–30 minutes rather than once a week for hours
- After each evaluation, focus on **one weak area at a time** — don't try to fix everything at once

---

## 9. Troubleshooting

**"Groq API key required" error**
Go to ⚙ Settings, paste your key (`gsk_...`), test it, and save. See [Section 2](#2-first-time-setup).

**"Invalid API key" when testing**
Make sure you copied the full key starting with `gsk_`, with no extra spaces. Recreate it on console.groq.com if needed.

**Speech generation or evaluation is slow / fails**
- If the platform hasn't been used in 15+ minutes, the backend may be "waking up" — this takes 2–3 minutes on the first request, then is fast again.
- If it's been fast before and suddenly errors, your Groq free-tier rate limit may be temporarily reached — wait a minute and retry.

**The recording button doesn't appear**
Your browser needs microphone permission — click the camera/microphone icon in the address bar, allow access, and reload.

**No audio plays after clicking "Generate audio"**
Make sure you're on the latest version of the page (hard refresh: Ctrl+Shift+R / Cmd+Shift+R). If it still doesn't play, try a different browser.

**Arabic text looks garbled**
Update your browser — Arabic needs a modern browser (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+).

**"No results found" in UN Library**
The library doesn't have a matching demo document for that exact topic/domain combination. Try a broader topic or a different domain, or just generate the speech without UN grounding.

---

## Quick reference

| Action | Where |
|---|---|
| Get in without an account | Login screen → **Continue as Guest** |
| Add/change your Groq API key | ⚙ Settings (gear icon, top nav) |
| Generate a speech | Module A — Generate speech |
| Listen to the speech | Module B — Audio & materials |
| Download the glossary | Module B → Generate materials → Download glossary |
| Record your interpretation | Module C — Record & transcribe |
| Get your score and feedback | Module D — Evaluation |
| Ask for help / technique advice | 💬 chat button, bottom-right |

---

*ETIB Interpreter Self-Training Platform — Final Year Project, ESIB, USJ Beirut, 2025–2026*
*Supervised by Prof. Lina Sader Feghali and Prof. Wadad Wazen Gergy*
