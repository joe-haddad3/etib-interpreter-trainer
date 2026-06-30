# ETIB — Technical Report
**Project:** Interpreter Self-Training Platform
**Institution:** ESIB–USJ, Lebanon
**Supervisors:** Prof. Lina Sader Feghali & Prof. Wadad Wazen Gergy
**Date:** June 2026
**Stack:** Flask · React (Vite) · MongoDB Atlas · edge-tts · faster-whisper · Groq (Llama 3.3 70B / Whisper)
**Deployment:** Vercel (frontend) + HuggingFace Spaces Docker (backend) — live, free tier, publicly reachable

---

## 1. What Works — All Four Modules Are Complete

### 1.1 Speech Generation — Module A
- Groq (Llama 3.3 70B) generates parametric speeches in Arabic, French, and English.
- Free-text topic input plus 12 domain presets: politics, diplomacy, economics, health, education, climate, human rights, **technology/AI**, migration, disarmament, women, food.
- Full parameter control: language, target language, domain, word count, difficulty, interpretation mode (consecutive/simultaneous/sight translation), hesitation density, pressure simulation (speed, topic shifts, cognitive load).
- Document-grounded generation: upload a PDF/DOCX, the platform extracts context via RAG (dense embedding retrieval with keyword fallback) and grounds the speech in it.
- UN Digital Library integration: search and select a real UN document as the speech source.

### 1.2 Text-to-Speech & Materials — Module B
- edge-tts (Microsoft Neural voices), multiple accents per language (Lebanese/Gulf/Egyptian Arabic; Parisian/Canadian French; US/UK/AU English).
- Speech rate adjustment.
- Pedagogical materials generation: key terms, thematic summary, MCQs, trilingual glossary (downloadable as DOCX).

### 1.3 Transcription — Module C
- Local faster-whisper (CPU, word-level timestamps + confidence scores) is the primary path — gives accurate segment boundaries needed for silence/repetition detection.
- Groq-hosted Whisper available as a fast alternative but does not return word timestamps (see §2.1).
- Tashkeel inference (Arabic diacritics) on the transcript, deliberately preserving the student's pronunciation errors rather than auto-correcting them.

### 1.4 Performance Evaluation — Module D
**Algorithmic detection (free, deterministic):**
- Long silences (segment-gap and word-gap based, with leading-silence detection)
- Repetitions (word + 2/3-word phrase level, language-aware comparison — see §2.4)
- Hesitation words per language, tuned per-language word lists (see §2.4)
- Low-confidence words (Whisper probability < 0.6)
- Number/date/statistic errors

**LLM analysis (Groq):** translation accuracy, content coverage, terminology, pronunciation flags, language-quality errors, auto-corrections, false starts, lapsus linguae, pause/repetition commentary, numbers cross-check. As of 2026-06-30 the prompt was rewritten to be strict — earlier versions gave students the benefit of the doubt and missed obvious mistranslations (see §2.5).

**Adaptive difficulty:** session history analysis recommends next-session difficulty, word count, number density, pace, and structure based on trends across the student's last 10–20 sessions.

### 1.5 Authentication & Access
- Signup/login (MongoDB-backed, token stored in DB so it survives backend restarts — see §2.6).
- **Guest login**: no email/password, immediate access, Groq key stored locally only.
- Single role: **student**. Instructor/Coordinator roles were removed — platform is student-self-training only.
- Per-user Groq API key (entered in Settings, stored in browser localStorage) — no shared server-side key, no shared quota risk.

### 1.6 Chat Assistant
- Floating widget available on every authenticated screen.
- System prompt gives it real platform/technique knowledge (module descriptions, consecutive/simultaneous/sight-translation theory, concrete problem→solution pairs) rather than generic LLM chit-chat.

### 1.7 Frontend
- Full trilingual UI (English/French/Arabic) with RTL layout for Arabic.
- All module panels live and wired to the backend; state persists across tab switches.
- In-browser audio recording (MediaRecorder API).
- Tashkeel toggle on Arabic transcripts.

### 1.8 Arabic Utilities
- Normalization (alef variants, ta marbuta, alef maksura), diacritic stripping, Arabic-Indic numeral conversion, code-switching detection.

---

## 2. Problems Found and Fixed

### 2.1 Groq Whisper loses word timestamps
**Problem:** Groq's hosted Whisper returns a clean transcript but no word-level timestamps, which silently breaks silence/repetition detection.
**Fix:** `/full-evaluation` re-transcribes locally with faster-whisper for accurate timestamps, then layers LLM analysis on top.

### 2.2 LLM responses are not reliably valid JSON
**Problem:** Groq frequently wraps JSON in markdown fences or prepends explanatory text.
**Fix:** A sanitizing extractor strips fences and isolates the `{...}` boundary before `json.loads()`.

### 2.3 CORS failures in production
**Problem:** `Access-Control-Allow-Credentials` errors — the HuggingFace Spaces reverse proxy strips all custom request headers except `Content-Type`, so any auth scheme relying on headers/cookies silently failed cross-origin.
**Fix:** Switched to token-in-body authentication (`auth_token` field in every JSON/form payload) and Groq key in body — zero custom headers required.

### 2.4 English/French evaluation false positives (fixed 2026-06-30)
**Problem:** `HESITATION_FILLERS['en']` included ordinary words ('so', 'well', 'right', 'okay', 'actually', 'basically'), generating massive false-positive hesitation counts on normal English speech. Separately, the repetition-comparison function stripped trailing 's' from *all* languages (a French-only liaison/plural quirk), causing English word pairs like "goes"/"go" or "days"/"day" to be flagged as repetitions.
**Fix:** Removed the non-hesitation words from the English filler list; gated the trailing-'s' strip to French only by threading a `language` parameter through `repetition_compare_key`, `words_are_repetition_equivalent`, `detect_repetitions`, and `detect_repetitions_from_text`.

### 2.5 Evaluation was too lenient on translation errors
**Problem:** The LLM prompt instructed the evaluator not to compare "word-for-word" and to accept "close equivalents," which caused it to silently forgive genuine mistranslations a professor would catch instantly.
**Fix:** Rewrote Task 1 of the evaluation prompt with an explicit "strict professor" framing, a concrete list of what counts as an error (wrong word choice, weakened meaning, wrong domain term, opposite meaning, approximate numbers), explicit rejection of "close enough" as an excuse, and a rule capping `overall_score` at 6 when 3+ errors are found.

### 2.6 Accounts and sessions lost on every backend restart
**Problem:** Auth tokens were stored in an in-memory Python dict; HuggingFace's free tier restarts the container after ~15 min of inactivity, wiping all logged-in sessions. Separately, MongoDB Atlas was rejecting connections from HF Spaces' dynamic IPs.
**Fix:** Tokens moved to a MongoDB `auth_tokens` collection (falls back to in-memory only if Mongo is unreachable); Atlas IP Access List set to `0.0.0.0/0` (required since HF Spaces has no fixed egress IP).

### 2.7 Session history was shared across all users
**Problem:** Module D used `flask_session.get('user_id', 'anonymous')`, but the app never sets Flask sessions (token-based auth, no cookies) — every user's evaluation history was being saved under the literal string `'anonymous'`, mixing all students' data together.
**Fix:** Added `_current_user_id()` which resolves the real user from the `auth_token` present in the request (args/form/JSON body) via `get_user_from_token()`.

### 2.8 UN Digital Library blocked from cloud IPs
**Problem:** `digitallibrary.un.org` sits behind an AWS WAF that silently 202-blocks requests from cloud-server TLS fingerprints (including HuggingFace Spaces).
**Fix:** Falls back to ~24 curated demo UN documents spanning the 12 supported domains. Returns an empty result set (not fabricated matches) when a searched topic has no real coverage, rather than silently substituting an unrelated topic — an earlier version of the fallback incorrectly returned climate-change documents for an "economics" search because it matched on the wrong query variable.

### 2.9 Module B audio playback silently broken in production
**Problem:** The "Generate audio" button in Module B built the playback URL with a hardcoded `http://127.0.0.1:5000` prefix. This worked only when running the backend on the developer's own machine; for every real deployed visitor it pointed at their own (nonexistent) localhost server, so the player always showed `0:00 / 0:00` with no audio and no visible error.
**Fix:** Exported the same configurable `SERVER_BASE` already used for all other API calls from `api.js` and used it to build the audio URL.

### 2.10 Production backend returning HTTP 500 / failed builds
**Problem:** The HuggingFace Space Docker build was fragile — `torchaudio` was installed separately from `torch` (version-conflict risk), and the requirements file pulled in three packages (`pdfminer.six`, `pypdfium2`, `tiktoken`) that are never imported anywhere in the codebase, adding build time and failure surface for no benefit.
**Fix:** Install `torch` and `torchaudio` together in the same `pip install` command; removed the three unused packages; relaxed over-pinned versions for `pypdf`/`Pillow` that risked pip resolution failures.

### 2.11 Naive Arabic tokenization
**Status — known limitation, not fixed:** Word counting and repetition detection use whitespace splitting, which is imprecise for Arabic because clitics attach to words. A dedicated Arabic NLP library (e.g. CAMeL Tools) would be more accurate but was deferred due to size/setup complexity.

### 2.12 Forced alignment (WhisperX) — partially wired, optional
**Status:** `modules/alignment.py` exists and lazily imports `whisperx` only inside function calls (not at module load), so a missing/broken whisperx install does not crash the app at startup. WhisperX is CPU-capable but slow; treated as an optional enhancement, not a hard dependency.

---

## 3. Deployment Architecture

```
Frontend (React/Vite)  →  Vercel  →  etib-interpreter-trainer.vercel.app
                                            │
                                            │  fetch (token in body, no cookies)
                                            ▼
Backend (Flask, Docker)  →  HuggingFace Spaces  →  joe-haddad3-etib-backend.hf.space
                                            │
                                            ▼
                                   MongoDB Atlas (M0 free tier, 0.0.0.0/0 IP access)
                                            │
                                            ▼
                                   Groq API (Llama 3.3 70B + Whisper) — per-user key
```

- **Two GitHub remotes** are pushed on every change: `deploy` (`joe-haddad3/etib-interpreter-trainer`, watched by Vercel) and `origin` (`chrisswhb/ETIB-Interpreter-Trainer`, team repo, push to `joe-main` — `main` is protected/PR-only).
- **Backend lives in a separate working copy** (`etib-hf-space/`) pushed to a third remote (`hf`, the HuggingFace Space git repo) — files are manually synced from the main repo's `backend/` folder before each backend commit, since HF Spaces does not support symlinked/shared sources.
- HuggingFace free tier sleeps after ~15 min idle; cold start takes 2–3 min.

---

## 4. Key Design Decisions

| Decision | Reason |
|---|---|
| Token-in-body auth instead of cookies/headers | HF Spaces' reverse proxy strips custom headers cross-origin; cookies require credentialed CORS the proxy doesn't support |
| Per-user Groq key instead of shared server key | No shared rate-limit/cost exposure; each student uses their own free quota |
| Algorithmic + LLM hybrid for evaluation | Algorithmic detection is free, deterministic, and catches what LLMs miss (exact silences/repetitions); LLM adds semantic depth |
| Strict-professor LLM evaluation prompt | Early version was too forgiving and missed obvious translation errors — defeats the purpose of an evaluator |
| Preserve student errors in tashkeel | Pedagogically necessary — correcting errors would hide evidence from the feedback module |
| Trilingual UI built from day one | Cahier des charges requirement; retrofitting RTL later is very difficult |
| Guest login alongside accounts | Lowers friction for professors/testers trying the platform without creating an account |
| Demo UN Library fallback returns empty rather than wrong-topic results | A wrong-but-confident result is worse for a training platform than an honest "no results" |

---

## 5. Known Limitations (for the demo / meeting)

- **Arabic evaluation is the weakest link** — ASR struggles with Lebanese Arabic/French code-switching, and the LLM's إعراب/تشكيل analysis is inconsistent. French/English evaluation is solid.
- **UN Library is demo data in production**, not live search (UN blocks cloud server IPs via WAF).
- **HuggingFace free tier cold start** — first request after 15 min idle takes 2–3 min.
- The platform should be presented as a **training aid that gives instant preliminary feedback**, not a replacement for professor grading.

---

*This document reflects the platform state as of 2026-06-30.*
