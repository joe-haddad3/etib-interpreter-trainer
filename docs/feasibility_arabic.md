# Arabic Language Feasibility Log

**Project:** ETIB Interpreter Self-Training Platform  
**Purpose:** Document honestly what works and what doesn't for Arabic AI tasks.  
This is a required deliverable. The client (Prof. Lina Sader Feghali) explicitly 
asked for a feasibility assessment. Do not skip this.

---

## Why this document exists

From the cahier des charges:
> "Nous sommes conscients que de tels outils ont des limites notamment quand 
> la langue arabe est l'une des langues de travail."

And:
> "La spécificité de cet outil réside dans la prise en charge des différentes 
> tâches en langue arabe."

Arabic is both the primary challenge and the primary differentiator of this project.

---

## How to use this document

Each team member adds their findings here as they discover them.
Use the sections below. Be specific — give examples of failures, not just ratings.

---

## Module A — LLM Speech Generation (Person 2)

### Test date:
### Model tested:
### Test parameters:

### Sample Arabic output:
```
[paste the Arabic script here]
```

### Quality checklist:
- [ ] Output is entirely in Arabic script (no Latin characters mixed in)
- [ ] Reads like a real conference speech (not a translated English text)
- [ ] Uses authentic oratory connectors (أيها السادة، وفي هذا الإطار، إن...)
- [ ] Numbers are correctly expressed in Arabic
- [ ] No dialect words (sticks to MSA / الفصحى)
- [ ] Diacritics used on difficult words (optional but welcome)

### Rating (1–10):
### Specific errors observed:
### Recommendation:

---

## Module B — TTS Arabic Voice Quality (Person 4)

### Test date:
### Tool tested: edge-tts
### Voices tested:

| Voice | Naturalness (1–10) | Accent | Specific issues |
|---|---|---|---|
| ar-LB-RamiNeural | | Lebanese male | |
| ar-LB-LaylaNeural | | Lebanese female | |
| ar-SA-ZariyahNeural | | Gulf female | |
| ar-EG-SalmaNeural | | Egyptian female | |
| ar-EG-ShakirNeural | | Egyptian male | |

### Best voice for this project:
### Main concern:
### Does any voice handle numbers naturally?

---

## Module C — ASR Arabic Transcription Quality (Person 5)

### Test date:
### Model: faster-whisper large-v3
### Audio source:

### Transcript produced:
```
[paste Whisper output here]
```

### Original text (what was said):
```
[paste the TTS input text here]
```

### Error analysis:
- Language correctly detected: Y / N
- Approximate word error rate (%): 
- Numbers transcribed correctly: Y / N / Partially
- Low-confidence words flagged: 
- Does it handle Lebanese accent: Y / N / Partially

### Speed (important for UX):
- Audio duration:
- Transcription time:
- Acceptable for async workflow (>2 min delay OK): Y / N

### Recommendation for Module C:

---

## Overall Arabic feasibility verdict

To be completed at end of Week 1 by the team lead.

| Component | Feasibility | Notes |
|---|---|---|
| LLM Arabic speech generation | 🟡 / 🟢 / 🔴 | |
| Arabic TTS (edge-tts) | 🟡 / 🟢 / 🔴 | |
| Arabic ASR (Whisper) | 🟡 / 🟢 / 🔴 | |
| Arabic LLM evaluation | 🟡 / 🟢 / 🔴 | |

🟢 Good enough for prototype  
🟡 Works but with notable limitations — document them  
🔴 Does not work well enough — needs alternative
