# ETIB — Technical Report
**Project:** Interpreter Self-Training Platform  
**Institution:** ESIB–USJ, Lebanon  
**Supervisors:** Prof. Lina Sader Feghali & Prof. Wadad Wazen Gergy  
**Date:** June 2026  
**Stack:** Flask · React (Vite) · MongoDB · edge-tts · faster-whisper · Groq (Llama 3.3 70B / Whisper)

---

## 1. What Worked

### 1.1 Speech Generation — Module A
- **Groq (Llama 3.3 70B)** produces high-quality parametric speeches in Arabic, French, and English.
- Arabic-specific prompt engineering enforces Modern Standard Arabic (الفصحى), authentic oratory connectors, and Arabic-Indic numerals (٠–٩). This was critical because without explicit constraints the model mixed in French/English words or used colloquial Arabic.
- Full parameter control: language, domain, word count, difficulty, interpretation mode (consecutive / simultaneous / sight translation), hesitation density.

### 1.2 Text-to-Speech — Module B
- **edge-tts (Microsoft Neural voices)** produced natural, intelligible speech across all three languages.
- Multiple accents available: Lebanese, Gulf, Egyptian for Arabic; Parisian, Canadian for French; American, British, Australian for English.
- Speech rate adjustment (−50 % to +50 %) lets instructors control difficulty.

### 1.3 Automatic Speech Recognition — Module C
- **Groq-hosted Whisper (large-v3)** transcribes student recordings in ~3 seconds, supporting all three languages.
- **faster-whisper (local, CPU)** used as a fallback when Groq is unavailable — slower (~1–3 min) but always works offline and returns word-level timestamps and confidence scores.
- **Tashkeel inference** (adding Arabic diacritics to the transcript) was implemented using an LLM post-processing step. The system deliberately preserves the student's errors in the diacritics rather than correcting them — this provides evidence of pronunciation mistakes for the feedback module.

### 1.4 Performance Evaluation — Module D
- **Algorithmic detection (no LLM, always free):**
  - Long silences (gaps > 1.5 s flagged as possible omissions)
  - Repetitions (consecutive duplicate words)
  - Hesitation words per language (Arabic: يعني، أقصد; French: euh, heu; English: um, uh)
  - Low-confidence words (Whisper probability < 0.6)
  - Number errors (Arabic-Indic numerals extracted and compared to source)
- **LLM analysis (Groq):** detects semantic errors — language errors, auto-corrections, false starts, lapsus linguae, terminology problems, information loss — and returns an overall score (0–10).
- **Arabic case-ending analysis (إعراب):** dedicated tashkeel-compare endpoint uses LLM to detect wrong case endings even when the audio lacks visible diacritics.

### 1.5 Authentication
- Signup / login / logout / session check — all working.
- MongoDB with a 2-second timeout and automatic fallback to in-memory storage so the app runs without a database server during development.

### 1.6 Frontend
- Full trilingual UI (English / French / Arabic) with RTL layout for Arabic.
- All four module panels rendered and wired to the backend.
- In-browser audio recording (MediaRecorder API) with optional file-upload fallback.
- Tashkeel toggle on transcripts (switch between plain and fully vocalized Arabic text).

### 1.7 Arabic Utilities
- Arabic normalization (alef variants, ta marbuta, alef maksura).
- Diacritic stripping for text comparison.
- Arabic-Indic numeral conversion.
- Code-switching detection (Arabic + Latin mixing ratio).

---

## 2. What Did Not Work / Required Workarounds

### 2.1 Groq Whisper Loses Word Timestamps
**Problem:** The Groq-hosted Whisper API returns a clean transcript but no word-level timestamps. Without timestamps, silence detection and repetition detection return zero results — the algorithmic evaluation is blind.  
**Workaround:** The `/full-evaluation` endpoint re-transcribes the audio locally with faster-whisper to obtain accurate segment boundaries and word timestamps, then layers the LLM analysis on top. This doubles transcription time but produces correct results.  
**Root cause documented in code:** Groq normalizes silence and repetitions away in its hosted version.

### 2.2 LLM Responses Are Not Reliably Valid JSON
**Problem:** Groq (and other LLMs) frequently wrap JSON output in markdown code fences (` ```json ... ``` `) or add an explanatory sentence before the JSON object. Direct `json.loads()` calls failed on these responses.  
**Workaround:** A JSON extraction utility strips markdown fences and finds the first `{` to last `}` boundary before parsing. Applied consistently in Module B (materials) and Module D (feedback, full-evaluation).  
**Lesson:** Never trust raw LLM output as valid JSON — always sanitize.

### 2.3 Groq API Availability and Cost
**Problem:** During development, Groq experienced occasional outages and rate-limit errors. Relying on a single LLM provider was not viable.  
**Workaround:** A three-tier fallback chain: Groq (free, fast) → Google AI Studio / Gemini 1.5 Flash (free) → OpenAI (paid, last resort). All three are configured in `config.py`.

### 2.4 Naive Arabic Tokenization
**Problem:** Counting Arabic words and detecting repetitions uses simple whitespace splitting. This is inaccurate because Arabic clitics attach to words (e.g., وَالْكِتَابُ is one token but semantically two words).  
**Status:** A comment in the code notes that CAMeL Tools (a dedicated Arabic NLP library) would be more accurate, but integrating it was deferred due to its size and setup complexity.  
**Impact:** Minor inaccuracies in word count and repetition detection for Arabic.

### 2.5 Forced Alignment Module Not Completed
**Problem:** A `/api/module-c/align` endpoint was planned to use WhisperX for forced alignment (mapping each word to an exact timestamp in the audio). The backend endpoint exists and imports from `modules.alignment`, but the `alignment.py` file was never created.  
**Status:** The endpoint is broken at import time if called. WhisperX requires PyTorch and a GPU for practical use, which exceeded the project's hardware constraints on the development machine.

### 2.6 TTS Voice Selection Pending Human Review
**Problem:** The Arabic, French, and English neural voices were chosen from Microsoft's catalogue without listening to all options. A comment in `config.py` notes that the final voice selection was left to team review after listening to samples.  
**Status:** Voices are functional but may not be the best choices for pedagogical use. A listening session with native speakers is recommended before submission.

### 2.7 Not Yet Implemented (Stubs)
The following endpoints return HTTP 501 and are planned for upcoming weeks:

| Endpoint | Feature | Assigned |
|---|---|---|
| `POST /api/module-a/from-document` | Generate speech from PDF/DOCX upload | Person 2 |
| `GET /api/module-d/history/<session_id>` | Session history + adaptive difficulty | Person 5 |

MongoDB schemas for session storage have not been designed yet, which blocks the history and adaptive difficulty features.

---

## 3. Key Design Decisions

| Decision | Reason |
|---|---|
| Fallback chain for every external service | Development machines had no GPU and internet was sometimes unavailable |
| Algorithmic + LLM hybrid for evaluation | Algorithmic detection is free and deterministic; LLM adds semantic depth |
| Preserve student errors in tashkeel | Pedagogically necessary — correcting errors would hide evidence from the feedback module |
| Trilingual UI built from day one | Cahier des charges requirement; retrofitting RTL is very difficult |
| edge-tts over cloud TTS APIs | Free, no API key required, high voice quality for all three target languages |

---

*This document will be updated as remaining stubs are implemented.*
