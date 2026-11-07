# ETIB — Interpreter Self-Training Platform

**AI-powered self-training platform for conference interpreter trainees**  
École de Traducteurs et d'Interprètes de Beyrouth — Université Saint-Joseph, Beirut

Working languages: **Arabic · French · English**

> **Live demo: [etib-interpreter-trainer.vercel.app](https://etib-interpreter-trainer.vercel.app)**
> Sign in or create an account. The backend runs on a free Hugging Face Space, so the first request after a period of inactivity can take 2–3 minutes while it wakes up.

---

## What it does

Students log in, generate a realistic conference speech (or upload a source document), listen to it via TTS, record their own interpretation, and receive instant AI feedback — all in one browser session.

| Module | What it produces |
|--------|-----------------|
| **A — Speech Generation** | Configurable training speech (topic, domain, length, difficulty, hesitations, number density, discourse structure) grounded in real UN documents when available |
| **B — Audio & Materials** | Edge-TTS audio with accent/speed control + key terms, thematic summary, MCQ, comprehension questions, trilingual glossary (AR/FR/EN), downloadable DOCX |
| **C — Transcription** | Groq Whisper-large-v3 ASR (falls back to local faster-whisper) + Arabic tashkeel of what the student actually said |
| **D — Evaluation** | Hesitation count, omission detection, number errors, terminology coverage, pronunciation alignment, LLM feedback paragraph, adaptive difficulty recommendations |
| **E — Progress** | Session history, score trend (last 10 sessions), focus areas, strengths, specific recurring errors |

---

## Architecture

```
Browser (React + Vite, hosted on Vercel)
  │  fetch() — JSON bodies, auth token in the body
  ▼
Flask backend  (Python 3.11, Docker on Hugging Face Spaces)
  ├── /api/module-a   →  LLM speech generation   (services/llm_service.py → Gemini)
  ├── /api/module-b   →  TTS (edge-tts) + materials (Gemini)
  ├── /api/module-c   →  ASR transcription (Groq Whisper / faster-whisper)
  ├── /api/module-d   →  Evaluation + feedback (Gemini) + sessions (MongoDB)
  ├── /api/library    →  UN Digital Library search + PDF download
  ├── /api/chat       →  Chat endpoint
  └── /api/auth       →  Login / signup
```

**Central server-side keys:** the backend holds the API keys (Gemini for text generation and evaluation, Groq for Whisper ASR). Students do not need an API key of their own, and no key is stored in or sent from the browser.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, plain CSS (no framework) |
| Backend | Flask 3, Python 3.11 |
| LLM | Google Gemini via REST API (default `gemini-3.5-flash-lite`); provider abstraction also supports Groq and local Aya models |
| ASR | Groq hosted `whisper-large-v3` → local `faster-whisper` fallback |
| TTS | `edge-tts` (Microsoft Azure Neural voices, free) |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers) for RAG |
| Database | MongoDB (local) with in-memory fallback for dev |
| UN Library | UN Digital Library MARCXML API + curl PDF download |
| Deployment | Vercel (frontend) · Hugging Face Spaces, Docker (backend) |

---

## Local setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- ffmpeg — `winget install ffmpeg` / `brew install ffmpeg` / `sudo apt install ffmpeg`
- MongoDB (optional — app runs without it, sessions stored in memory)

### 1 — Clone and configure

```bash
git clone https://github.com/joe-haddad3/etib-interpreter-trainer.git
cd etib-interpreter-trainer
```

Copy `backend/.env.example` to `backend/.env` and fill in at least:

```env
LLM_PROVIDER=gemini
GOOGLE_AI_KEY=your_google_ai_key_here   # Gemini: text generation and evaluation
GROQ_API_KEY=your_groq_api_key_here     # Groq: Whisper speech-to-text
FLASK_SECRET_KEY=change-me-in-production
FLASK_DEBUG=true
UPLOAD_FOLDER=./uploads
AUDIO_OUTPUT_FOLDER=./audio_outputs
# MONGODB_URI is optional; without it, sessions are kept in memory
```

Never commit `backend/.env`.

### 2 — Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python app.py
# → http://127.0.0.1:5000
```

### 3 — Frontend

```bash
cd Frontend
npm install
npm run dev
# → http://localhost:5173
```

Open `http://localhost:5173` in your browser.

---

## API keys

The platform runs on **central server-side keys**, set as environment variables on the backend (`GOOGLE_AI_KEY` for Gemini, `GROQ_API_KEY` for Whisper ASR). They are never stored in the repository. Students sign in with an account; they never handle API keys.

Free-tier quotas of both providers change over time, so check the current limits on [Google AI Studio](https://ai.google.dev) and [console.groq.com](https://console.groq.com) before load testing.

---

## Project structure

```
etib-interpreter-trainer/
├── backend/
│   ├── app.py                  # Flask app, blueprints, CORS
│   ├── config.py               # All env vars and constants
│   ├── Dockerfile              # Hugging Face Spaces image (port 7860)
│   ├── requirements.txt
│   ├── modules/
│   │   ├── module_a.py         # Speech generation (LLM + RAG + UN grounding)
│   │   ├── module_b.py         # TTS + pedagogical materials
│   │   ├── module_c.py         # ASR transcription + tashkeel
│   │   ├── module_d.py         # Evaluation, feedback, sessions, adaptive params
│   │   ├── module_library.py   # UN Digital Library search + fetch
│   │   ├── alignment.py        # WhisperX forced alignment + LLM analysis
│   │   ├── chat.py             # Chat endpoint
│   │   └── auth.py             # Login and signup
│   ├── services/
│   │   ├── llm_service.py      # LLM provider abstraction (Gemini / Groq / local Aya)
│   │   └── terminology.py      # Terminology helpers
│   ├── utils/                  # Groq client, RAG retrieval, UN documents, Arabic utils
│   └── tests/                  # pytest tests (ASR, auth, TTS, Module A)
├── Frontend/
│   ├── src/
│   │   ├── App.jsx             # All React components + UI strings (EN/AR/FR)
│   │   └── api.js              # All fetch helpers (auth token sent in the JSON body)
│   ├── styles/
│   │   ├── main.css
│   │   └── rtl.css
│   └── index.html
└── docs/
    ├── USER_GUIDE.md           # Student + instructor guide
    ├── technical_report.md     # Deployment and engineering notes
    └── ...
```

---

## Module A — Speech generation (technical notes)

- **RAG pipeline**: source document is chunked (1 800 chars, 250 overlap) → embedded with `paraphrase-multilingual-MiniLM-L12-v2` → top-4 chunks by cosine similarity injected into the LLM prompt
- **UN grounding**: searches UN Digital Library MARCXML API → downloads the document PDF → extracts text → same RAG pipeline
- **Arabic numerals**: all digit sequences in AR speeches are converted to Eastern Arabic-Indic (٠١٢٣٤٥٦٧٨٩)
- **Factual accuracy**: when no UN document is found, the prompt includes explicit rules against inventing statistics

## Module D — Evaluation (technical notes)

- **Hesitations**: detected by regex in transcript (`euh`, `um`, `آه`, `يعني`, ...)
- **Number errors**: compares number tokens in source vs. transcript
- **Omissions**: silence gaps > 500 ms in audio flagged as possible omissions
- **Adaptive params**: after each session, recomputes recommended difficulty/length/domain based on score trends; tracks `problems_to_work_on` and `top_errors`
- **Sessions**: stored in MongoDB (`etib_interpreter_trainer.sessions`); falls back to in-memory dict if MongoDB is unavailable

---

## Project context

Built during an 8-week summer internship (June–July 2026) at Université Saint-Joseph de Beyrouth (ESIB · ETIB · CINIA) by a team of six students from ESIB's AI option, with USJ's School of Translators and Interpreters (ETIB) as the client. The platform was refined after the internship based on ETIB feedback (August–September 2026).

**Supervisors (ETIB):** Prof. Lina Sader Feghali · Prof. Wadad Wazen Gergy
