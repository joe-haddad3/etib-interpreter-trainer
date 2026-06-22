# ETIB — Interpreter Self-Training Platform

**AI-powered self-training platform for conference interpreter trainees**  
École de Traducteurs et d'Interprètes de Beyrouth — Université Saint-Joseph, Beirut

Working languages: **Arabic · French · English**

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
Browser (React + Vite)
  │  fetch() with X-Groq-Api-Key header
  ▼
Flask backend  (Python 3.11)
  ├── before_request  →  flask.g.groq_api_key
  ├── /api/module-a   →  LLM speech generation   (llm_service.py → Groq)
  ├── /api/module-b   →  TTS (edge-tts) + materials (Groq)
  ├── /api/module-c   →  ASR transcription (Groq Whisper / faster-whisper)
  ├── /api/module-d   →  Evaluation + feedback (Groq) + sessions (MongoDB)
  ├── /api/library    →  UN Digital Library search + PDF download
  └── /api/auth       →  Login / signup / validate-groq-key
```

**No server-side Groq key** — each student supplies their own free key via the Settings modal. The key lives only in their browser (`localStorage`) and is sent per-request.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, plain CSS (no framework) |
| Backend | Flask 3, Python 3.11 |
| LLM | Groq API — `llama-3.3-70b-versatile` (speech gen, evaluation, feedback) |
| ASR | Groq hosted `whisper-large-v3` → local `faster-whisper` fallback |
| TTS | `edge-tts` (Microsoft Azure Neural voices, free) |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers) for RAG |
| Database | MongoDB (local) with in-memory fallback for dev |
| UN Library | UN Digital Library MARCXML API + curl PDF download |

---

## Local setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- ffmpeg — `winget install ffmpeg` / `brew install ffmpeg` / `sudo apt install ffmpeg`
- MongoDB (optional — app runs without it, sessions stored in memory)

### 1 — Clone and configure

```bash
git clone https://github.com/chrisswhb/ETIB-Interpreter-Trainer.git
cd ETIB-Interpreter-Trainer
git checkout joe-main
```

Create `backend/.env`:

```env
LLM_PROVIDER=groq
FLASK_SECRET_KEY=change-me-in-production
FLASK_DEBUG=true
UPLOAD_FOLDER=./uploads
AUDIO_OUTPUT_FOLDER=./audio_outputs
# GROQ_API_KEY is intentionally omitted — students supply their own key
```

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

## API key model

This project uses a **per-student key** model:

1. Every student gets a **free** Groq API key at [console.groq.com](https://console.groq.com)
2. They paste it once in the **Settings** modal (gear icon ⚙ in the nav bar)
3. The key is saved in their browser's `localStorage` — never on the server
4. Every request sends `X-Groq-Api-Key: gsk_...` as an HTTP header
5. Flask reads it in `before_request` → `flask.g.groq_api_key`
6. `backend/utils/groq_client.py` uses only that key — no server fallback

To restore the shared-key approach (one server key for all students), switch to the `api-key-commun` branch.

---

## Groq free tier limits (as of 2026)

| Model | Requests/min | Tokens/min | Tokens/day |
|-------|-------------|------------|------------|
| llama-3.3-70b-versatile | 30 | 12 000 | 100 000 |
| whisper-large-v3 | 20 | — | 2 000 audio-sec |

A typical session (generate + transcribe + evaluate) uses ~3 000–5 000 tokens. The free tier supports roughly **20–30 full sessions per day** per student key.

---

## Branches

| Branch | Purpose |
|--------|---------|
| `joe-main` | Main development branch — all features |
| `api-key-commun` | Backup: shared server-key approach (no per-student key) |
| `kevin-main` | Kevin's contributions (merged into joe-main) |

---

## Project structure

```
ETIB-Interpreter-Trainer/
├── backend/
│   ├── app.py                  # Flask app, blueprints, CORS, before_request
│   ├── config.py               # All env vars and constants
│   ├── requirements.txt
│   ├── modules/
│   │   ├── module_a.py         # Speech generation (LLM + RAG + UN grounding)
│   │   ├── module_b.py         # TTS + pedagogical materials
│   │   ├── module_c.py         # ASR transcription + tashkeel
│   │   ├── module_d.py         # Evaluation, feedback, sessions, adaptive params
│   │   ├── module_library.py   # UN Digital Library search + fetch
│   │   ├── alignment.py        # WhisperX forced alignment + LLM analysis
│   │   └── auth.py             # Login, signup, validate-groq-key
│   ├── services/
│   │   └── llm_service.py      # LLM provider abstraction (Groq / Gemini / local)
│   └── utils/
│       └── groq_client.py      # Per-request Groq client factory
├── Frontend/
│   ├── src/
│   │   ├── App.jsx             # All React components + UI strings (EN/AR/FR)
│   │   └── api.js              # All fetch helpers with groqHeaders()
│   ├── styles/
│   │   ├── main.css
│   │   └── rtl.css
│   └── index.html
└── docs/
    ├── USER_GUIDE.md           # Student + instructor guide
    └── ...
```

---

## Module A — Speech generation (technical notes)

- **RAG pipeline**: source document is chunked (1 800 chars, 250 overlap) → embedded with `paraphrase-multilingual-MiniLM-L12-v2` → top-4 chunks by cosine similarity injected into the LLM prompt
- **UN grounding**: searches UN Digital Library MARCXML API → downloads PDF with browser User-Agent (WAF bypass) → extracts text → same RAG pipeline
- **Arabic numerals**: all digit sequences in AR speeches are converted to Eastern Arabic-Indic (٠١٢٣٤٥٦٧٨٩)
- **Factual accuracy**: when no UN document is found, the prompt includes explicit rules against inventing statistics

## Module D — Evaluation (technical notes)

- **Hesitations**: detected by regex in transcript (`euh`, `um`, `آه`, `يعني`, ...)
- **Number errors**: compares number tokens in source vs. transcript
- **Omissions**: silence gaps > 500 ms in audio flagged as possible omissions
- **Adaptive params**: after each session, recomputes recommended difficulty/length/domain based on score trends; tracks `problems_to_work_on` and `top_errors`
- **Sessions**: stored in MongoDB (`etib_interpreter_trainer.sessions`); falls back to in-memory dict if MongoDB is unavailable

---

## Supervisors

Prof. Lina Sader Feghali · Prof. Wadad Wazen Gergy — ETIB, USJ Beirut

Final Year Project — ESIB, Université Saint-Joseph, 2025–2026
