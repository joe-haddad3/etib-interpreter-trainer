# ETIB — Interpreter Self-Training Platform
### أداة الذكاء الاصطناعي للتدريب الذاتي للمترجمين الفوريين

AI-powered self-training platform for conference interpreter trainees at  
**ETIB — École de Traducteurs et d'Interprètes de Beyrouth, USJ**.

Working languages: **Arabic · French · English**

---

## Project overview

This platform allows trainee interpreters to:
- Generate realistic training speeches (AR/FR/EN) with configurable parameters
- Receive audio playback via Text-to-Speech
- Record their own interpretation and get it transcribed
- Receive automated performance feedback

Built as a Final Year Project for ESIB – USJ, supervised by  
**Prof. Lina Sader Feghali** and **Prof. Wadad Wazen Gergy**.

---

## Team

| Role | Responsibility |
|---|---|
| Person 1 | DevOps · Project lead · Repo setup |
| Person 2 | Backend · Module A (LLM speech generation) |
| Person 3 | Frontend · UI · Arabic RTL support |
| Person 4 | Module B (TTS + pedagogical materials) |
| Person 5 | Module C (ASR transcription) · Module D (evaluation) |

---

## Architecture

```
┌─────────────────────────────────────────────┐
│         Web Interface (Flask + HTML/JS)      │
│              Arabic + English UI             │
└──────┬──────────┬───────────┬───────────────┘
       │          │           │
  Module A   Module B    Module C + D
  LLM gen     TTS +       ASR +
  speeches   pedagogy   evaluation
```

---

## Quick start

### Prerequisites
- Python 3.10+
- ffmpeg (`brew install ffmpeg` / `sudo apt install ffmpeg`)
- Git

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/etib-interpreter-platform.git
cd etib-interpreter-platform
git checkout develop

# 2. Create Python environment
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cd ..
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (free at console.groq.com)

# 5. Run the backend
cd backend
python app.py
# Server starts at http://localhost:5000

# 6. Open the frontend
# Open frontend/index.html in your browser
```

### Test the API

```bash
# Health check
curl http://localhost:5000/health

# Generate an Arabic speech
curl -X POST http://localhost:5000/api/module-a/generate \
  -H "Content-Type: application/json" \
  -d '{"language":"ar","domain":"climate","word_count":200}'
```

---

## Branching strategy (Gitflow)

| Branch | Purpose |
|---|---|
| `main` | Production-ready code only. Protected — requires PR + review. |
| `develop` | Integration branch. All features merge here first. |
| `feature/XXX` | One branch per feature. Branch from `develop`. |

**Never commit directly to `main` or `develop`.**

```bash
# Start a new feature
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# When done
git push origin feature/your-feature-name
# Open a Pull Request on GitHub targeting develop
```

---

## Module status

| Module | Description | Status |
|---|---|---|
| A | LLM speech generation | 🔧 In progress |
| B | TTS + pedagogical materials | ⏳ Planned |
| C | ASR transcription | ⏳ Planned |
| D | AI evaluation + feedback | ⏳ Planned |

---

## Standards compliance

Per the project cahier des charges:
- **GDPR** — user data anonymized, minimal collection
- **ISO/IEC 27001** — action logging, secure key storage
- **IEEE 12207** — Git version control, testing coverage ≥80%
- **ISO 9241** — consistent UI design, RTL support

---

## Documentation

| Document | Location |
|---|---|
| Feasibility notes (Arabic AI) | `docs/feasibility_arabic.md` |
| TTS voice evaluation | `docs/tts_evaluation.md` |
| ASR evaluation | `docs/asr_evaluation.md` |
| Meeting minutes | `docs/meeting_minutes/` |
| Project description form | `docs/references/` |

---

## Key references

- Cahier des charges: `docs/references/ProjetETIB_2026_Cahierdescharges.docx`
- Project description form: `docs/references/ETIB_SelfTraining_Interpretation.docx`
- Fantinuoli, C. (2023). *Empowering autonomous learning through AI.*
- Wiedenmayer, A. (2026). *AI as a pedagogical tool for speech generation in interpreter training.*
