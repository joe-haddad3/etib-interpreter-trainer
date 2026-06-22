# ETIB Interpreter Trainer — User Guide

**École de Traducteurs et d'Interprètes de Beyrouth, USJ Beirut**

This guide explains how to use the ETIB Interpreter Self-Training Platform as a student or instructor. No technical knowledge is required.

---

## Table of contents

1. [First-time setup — get your API key](#1-first-time-setup)
2. [Create an account and log in](#2-create-an-account-and-log-in)
3. [Module A — Generate a training speech](#3-module-a--generate-a-training-speech)
4. [Module B — Listen to the speech and get study materials](#4-module-b--listen-and-study)
5. [Module C — Record your interpretation](#5-module-c--record-your-interpretation)
6. [Module D — Get your evaluation](#6-module-d--get-your-evaluation)
7. [Module E — Track your progress](#7-module-e--track-your-progress)
8. [Tips for effective practice](#8-tips-for-effective-practice)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. First-time setup

The platform uses **Groq** to generate speeches and evaluate your performance. Groq is free — you just need your own personal key.

### Step 1 — Create a free Groq account

1. Go to **[console.groq.com](https://console.groq.com)**
2. Sign up with your email address (it's free, no credit card needed)
3. Once logged in, go to **API Keys** in the left menu
4. Click **Create API key**, give it a name (e.g. "ETIB"), and copy the key — it starts with `gsk_`

> Keep your key private. Do not share it with anyone. If it leaks, delete it on console.groq.com and create a new one.

### Step 2 — Add your key to the platform

1. Open the ETIB platform in your browser
2. Log in to your account (or create one — see section 2)
3. Click the **⚙** (gear icon) in the top navigation bar — this opens **Settings**
4. Paste your key in the field that says `gsk_...`
5. Click **Test key** to verify it works — you should see "Key is valid and working"
6. Click **Save key**

Your key is saved in your browser only. No one else — not other students, not the server — can see it.

---

## 2. Create an account and log in

1. Open the platform in your browser
2. Click **Create an account**
3. Enter your full name, email, and a password (at least 8 characters)
4. Select your role: **Student**, **Instructor**, or **Coordinator**
5. Click **Create account** — you are logged in automatically

Next time, use **Sign in** with your email and password.

---

## 3. Module A — Generate a training speech

This is where you create the speech you will interpret.

### Basic generation (topic-only)

1. Click **Generate speech** in the navigation bar
2. Choose the **Speech language** (the language the speaker will use: AR, FR, or EN)
3. Choose the **Target language** (the language you will interpret into)
4. Type a **Topic** (e.g. "climate change", "digital health", "water scarcity")
5. Choose a **Domain** (Politics, Economy, Environment, Health, Law, Technology, Education, Diplomacy)
6. Adjust the settings you want:

| Setting | What it does |
|---------|-------------|
| Speech length | Short (~150 words), Medium (~250), Long (~350) |
| Difficulty | Beginner, Intermediate, Advanced, Expert |
| Discourse structure | Argumentative, Narrative, Descriptive, Mixed |
| Interpretation mode | Consecutive, Simultaneous, Sight translation |
| Number density | Controls how many figures and statistics appear |
| Hesitations | Adds natural "euh", "um", "يعني" fillers |
| Pressure mode | Speed pressure, topic shifts, cognitive load |

7. Click **Generate speech**

The speech appears below. A note tells you whether it was grounded in a real UN document.

### Document-grounded generation

Upload a PDF, Word, or text file as the source. The platform extracts key content from your document using AI (RAG) and builds the speech around it.

1. Expand **Document grounding**
2. Click **Choose file** and upload your document
3. Adjust settings as usual
4. Click **Generate from document**

You can also click **Preview retrieved context** to see exactly which passages the AI found in your document before generating.

### UN Library

Click **UN Library** to search real United Nations speeches and documents. When you select one, it is used as the grounding source for your generated speech — the content will be factually accurate and based on an actual UN document.

---

## 4. Module B — Listen and study

After generating a speech in Module A, click **Audio & materials** in the navigation bar.

### Audio playback

1. Choose a **voice accent** (Lebanese Arabic, Gulf Arabic, Parisian French, etc.)
2. Adjust the **speech rate** if you want it slower or faster
3. Click **Generate audio** — the audio player appears
4. Listen to the speech as if you were in a booth

### Pedagogical materials

Click **Generate materials** to get:

| Material | Description |
|----------|-------------|
| Key terms | 5 important domain-specific terms from the speech |
| Thematic summary | A visual tree structure of the main ideas |
| MCQ | 2–3 multiple-choice comprehension questions with answers |
| Open questions | Discussion questions about the speech content |
| Trilingual glossary | AR · FR · EN equivalents for the key terms |

Click **Download glossary (DOCX)** to save the glossary as a Word file you can edit and study offline.

---

## 5. Module C — Record your interpretation

1. Click **Record & transcribe** in the navigation bar
2. Select the **language of your interpretation** (not the source — the language you are speaking in)
3. Click the **record button** and start interpreting
4. Click **Stop** when you are done
5. Click **Transcribe** — the AI converts your speech to text (takes 5–15 seconds with Groq, up to 2 minutes with the local fallback)

The transcript appears with timestamps. For Arabic, the system also adds **tashkeel** (vowel diacritics) to show what you actually pronounced — including any case-ending errors.

Low-confidence words are highlighted — these are words the AI was uncertain about, which may indicate pronunciation issues.

---

## 6. Module D — Get your evaluation

Click **Evaluation** in the navigation bar. This module compares your recorded interpretation against the original speech.

### Full evaluation (recommended)

1. Make sure you have a generated speech from Module A
2. Click **Evaluate** after recording in Module C — or upload an audio file
3. Wait for the analysis (usually 10–20 seconds)

### What you get

**Scores (0–100):**

| Score | What it measures |
|-------|-----------------|
| Overall | Combined performance score |
| Fluency | How smooth your delivery was (fewer hesitations = higher) |
| Coverage | How much of the source content you conveyed |
| Numbers | Accuracy of numbers, dates, and statistics |

**Error breakdown:**
- Hesitations detected (euh, um, يعني, آه, ...)
- Omissions — content from the source you missed
- Number errors — figures you got wrong or skipped
- Terminology issues — key terms not used

**AI feedback paragraph** — a written explanation of your main strengths and what to improve

**Pronunciation report** — (Arabic) word-by-word confidence scores; words flagged as potentially mispronounced are analysed for likely tashkeel/إعراب errors

### Adaptive recommendations

After completing a session, the platform analyses your recent history and recommends:
- A speech **difficulty** level suited to your current level
- A **speech length** that challenges you without overwhelming
- A **domain** to focus on based on your weakest results

Click **Apply these settings** in Module E to use the recommended parameters next time.

---

## 7. Module E — Track your progress

Click **Progress** in the navigation bar.

### What you see

- **Latest session** — your most recent scores at a glance
- **Score trend** — a chart of your last 10 sessions showing improvement or decline
- **Focus areas** — the specific skills declining or stable that you should work on
- **Strengths** — areas where you are consistently performing well
- **Specific errors** — your most frequent recurring mistakes
- **Recommendations** — difficulty and domain suggestions from the AI

Progress is tracked automatically every time you complete a full evaluation in Module D.

---

## 8. Tips for effective practice

**Getting the most out of Module A:**
- Use **Advanced** difficulty once you can consistently score above 75 on **Intermediate**
- Turn on **Hesitations** to simulate real speaker conditions
- Use **Number density: High** if you struggle with figures — this is a common weak point
- Try the **UN Library** for authentic content on real UN topics

**Getting the most out of Module B:**
- Study the **key terms** before listening — it reduces cognitive load during interpretation
- Read the **thematic summary** to build your mental map of the speech
- Download and review the **glossary** the evening before a practice session

**Getting the most out of Module C:**
- For simultaneous interpretation, start recording as soon as you hear the first sentence
- For consecutive, take the speech segment by segment if you prefer
- Speak clearly — the ASR model works better with clear articulation

**Getting the most out of Module D:**
- Always use **full evaluation** (with audio) — it gives you the complete picture
- Focus on **one score at a time**. If fluency is low, prioritise reducing hesitations in the next session
- Read the AI feedback paragraph carefully — it identifies patterns across your errors

**General:**
- Practice **every day** for 20–30 minutes rather than once a week for 2 hours
- After each session, look at your **Focus areas** in Module E and choose your next speech topic accordingly
- The platform tracks progress automatically — you do not need to do anything extra

---

## 9. Troubleshooting

### "No Groq API key found" error

You have not saved your personal API key yet. Go to **⚙ Settings**, paste your key (`gsk_...`), test it, and save it. See [Section 1](#1-first-time-setup).

### "Invalid API key" when testing

- Make sure you copied the full key starting with `gsk_`
- Keys expire if you delete them on console.groq.com — create a new one if needed
- Do not add spaces before or after the key

### Speech generation is slow

Normal generation takes 5–15 seconds. If it takes longer than 30 seconds, your Groq free-tier rate limit may have been reached. Wait 1 minute and try again.

### Transcription is very slow (2+ minutes)

Your Groq key may have reached the audio transcription limit (2 000 seconds/day). The platform falls back to a local model automatically — it is slower but works without the key. Wait until the next day to use Groq Whisper again.

### The recording button does not appear

Your browser needs microphone permission. Click the camera/microphone icon in your browser's address bar and allow access, then reload the page.

### Arabic text looks garbled

Make sure your browser is up to date. Arabic requires a modern browser (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+).

### Scores seem too low

The platform is calibrated for conference interpreter training standards. A score of 60–70 is solid for a first attempt. Focus on consistency across sessions rather than a single high score.

### "No matching UN document was found"

The UN Library search did not find a document matching your topic and language combination. The speech is generated without source grounding but includes factual accuracy guidelines. Try a more specific topic or a different language.

---

## Quick reference

| Action | Where |
|--------|-------|
| Add/change your Groq API key | ⚙ Settings (gear icon in nav bar) |
| Generate a speech | Module A — Generate speech |
| Listen to the speech | Module B — Audio & materials |
| Download the glossary | Module B → Generate materials → Download glossary |
| Record your interpretation | Module C — Record & transcribe |
| Get your score and feedback | Module D — Evaluation |
| See your history and trends | Module E — Progress |
| Apply AI-recommended settings | Module E → Apply these settings |

---

*ETIB Interpreter Self-Training Platform — Final Year Project, ESIB, USJ Beirut, 2025–2026*  
*Supervised by Prof. Lina Sader Feghali and Prof. Wadad Wazen Gergy*
