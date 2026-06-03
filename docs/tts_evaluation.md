# TTS Voice Evaluation

**Responsible:** Person 4  
**Tool:** edge-tts (Microsoft Edge neural voices, no API key required)  
**Script:** `backend/tests/test_tts.py`

---

## Rating scale

| Score | Meaning |
|---|---|
| 1–3 | Unacceptable — robotic, unintelligible, or incorrect language |
| 4–6 | Acceptable for basic practice — noticeable artifacts |
| 7–8 | Good — natural enough for student self-training |
| 9–10 | Excellent — near-human quality |

---

## Arabic voices

| Voice | File | Naturalness | Accent | Notes |
|---|---|---|---|---|
| ar-LB-RamiNeural | tts_ar_LB_male.mp3 | /10 | Lebanese male | |
| ar-LB-LaylaNeural | tts_ar_LB_female.mp3 | /10 | Lebanese female | |
| ar-SA-ZariyahNeural | tts_ar_SA_female.mp3 | /10 | Gulf female | |
| ar-EG-SalmaNeural | tts_ar_EG_female.mp3 | /10 | Egyptian female | |
| ar-EG-ShakirNeural | tts_ar_EG_male.mp3 | /10 | Egyptian male | |

**Best Arabic voice:**  
**Main concern for Arabic:**  
**Does any voice handle numbers well?**  

---

## French voices

| Voice | File | Naturalness | Notes |
|---|---|---|---|
| fr-FR-DeniseNeural | tts_fr_FR_female.mp3 | /10 | |
| fr-FR-HenriNeural | tts_fr_FR_male.mp3 | /10 | |

**Best French voice:**  

---

## English voices

| Voice | File | Naturalness | Notes |
|---|---|---|---|
| en-US-JennyNeural | tts_en_US_female.mp3 | /10 | |
| en-GB-SoniaNeural | tts_en_GB_female.mp3 | /10 | |

**Best English voice:**  

---

## Speed control test

Test edge-tts rate parameter at -20%, 0%, +20% on the same Arabic text.  
Does the voice remain natural at slower speeds (important for beginners)?

| Rate | Naturalness | Usable? |
|---|---|---|
| -20% (slower) | /10 | |
| +0% (normal) | /10 | |
| +20% (faster) | /10 | |

---

## Final recommendation

**Chosen voice for AR:** `ar-LB-RamiNeural` ← update if different  
**Chosen voice for FR:** `fr-FR-DeniseNeural` ← update if different  
**Chosen voice for EN:** `en-US-JennyNeural` ← update if different  

**Should we look at Google Cloud TTS as fallback?** Y / N  
**Reason:**
