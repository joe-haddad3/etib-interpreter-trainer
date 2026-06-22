"""
Forced Alignment Service — Arabic Pronunciation Assessment
==========================================================
Uses WhisperX + WAV2VEC2-XLSR-53-Arabic to align student audio
against an expected (vocalized) reference text.

This is the approach recommended in the project research documents:
  "Expected Arabic sentence + User audio → Forced alignment →
   Detect wrong vowel ending"

Reference: Voice Processing for Police Hotlines (Nasr, Chamoun, USJ 2023)
           uses the same XLSR-Wav2Vec2 model for Lebanese Arabic.

Pipeline:
  1. Student audio → Groq Whisper → word transcript + timestamps
  2. WhisperX forced alignment → word-level confidence scores
  3. Compare low-confidence words against vocalized source text
  4. LLM analysis → identify specific case ending / tashkeel errors

Limitation (documented honestly):
  Short Arabic vowels (ُ َ ِ ً ٍ ٌ) are not in standard ASR vocabulary
  because Arabic is normally written unvocalized. We can flag WHICH WORDS
  had uncertain pronunciation, and use grammar context to infer the likely
  error — but we cannot directly measure which vowel was spoken.
"""
import os
import json
import re

ALIGN_MODEL    = None
ALIGN_METADATA = None
ALIGN_AVAILABLE = None   # None = not yet checked


def _check_whisperx() -> bool:
    """Return True if whisperx is installed and functional."""
    global ALIGN_AVAILABLE
    if ALIGN_AVAILABLE is not None:
        return ALIGN_AVAILABLE
    try:
        import whisperx  # noqa: F401
        ALIGN_AVAILABLE = True
        print('[Alignment] whisperx available ✓')
    except ImportError:
        ALIGN_AVAILABLE = False
        print('[Alignment] whisperx not installed — pronunciation alignment unavailable')
    return ALIGN_AVAILABLE


def get_align_model():
    """Load and cache the Arabic WAV2VEC2 alignment model (downloads once ~1.2 GB)."""
    global ALIGN_MODEL, ALIGN_METADATA
    if ALIGN_MODEL is None:
        import whisperx
        print('[Alignment] Loading Arabic WAV2VEC2 forced-alignment model...')
        print('[Alignment] First run: downloading ~1.2 GB — please wait...')
        ALIGN_MODEL, ALIGN_METADATA = whisperx.load_align_model(
            language_code='ar', device='cpu'
        )
        print('[Alignment] Alignment model ready ✓')
    return ALIGN_MODEL, ALIGN_METADATA


def align_words(audio_path: str, segments: list) -> list:
    """
    Run WhisperX forced alignment on already-transcribed segments.
    Returns segments enriched with precise word timestamps and confidence scores.

    args:
      audio_path : path to the student's audio file
      segments   : list of dicts from Whisper transcription
                   [{ start, end, text, words: [{word, start, end, probability}] }]

    returns:
      aligned_segments : same structure but with more precise word timestamps
                         and a per-word 'score' field (0–1, higher = more confident)
    """
    if not _check_whisperx():
        return segments   # return original if whisperx not available

    try:
        import whisperx
        model_a, metadata = get_align_model()
        audio = whisperx.load_audio(audio_path)

        # whisperx.align expects segments in its internal format
        result = whisperx.align(segments, model_a, metadata, audio, device='cpu',
                                return_char_alignments=False)
        return result.get('segments', segments)

    except Exception as e:
        print(f'[Alignment] align_words failed: {e}')
        return segments


def extract_word_scores(aligned_segments: list) -> list:
    """
    Flatten all words from aligned segments into a single list with scores.
    Returns: [{ word, start, end, score }]
    """
    words = []
    for seg in aligned_segments:
        for w in seg.get('words', []):
            # whisperx uses 'score', faster-whisper uses 'probability'
            score = w.get('score', w.get('probability', 1.0))
            words.append({
                'word':  w.get('word', '').strip(),
                'start': round(w.get('start', 0), 2),
                'end':   round(w.get('end', 0), 2),
                'score': round(score, 3)
            })
    return [w for w in words if w['word']]


def compare_against_source(
    aligned_words: list,
    source_text:   str,
    language:      str = 'ar',
    groq_api_key:  str = None,
    llm_model:     str = 'llama-3.3-70b-versatile',
    threshold:     float = 0.65
) -> dict:
    """
    Compare aligned words (with confidence scores) against the vocalized
    source text. Uses LLM to identify specific tashkeel / إعراب errors
    for uncertain words.

    returns:
      {
        words:          list  all words with scores and color grade
        uncertain:      list  words with score < threshold
        llm_analysis:   list  LLM-identified errors for uncertain words
        overall_score:  float mean pronunciation confidence (0–1)
      }
    """
    if not aligned_words:
        return {'words': [], 'uncertain': [], 'llm_analysis': [], 'overall_score': 0}

    # Color-grade each word
    graded = []
    for w in aligned_words:
        s = w['score']
        grade = 'good' if s >= 0.8 else ('warn' if s >= threshold else 'poor')
        graded.append({**w, 'grade': grade})

    uncertain = [w for w in graded if w['grade'] == 'poor']
    overall   = round(sum(w['score'] for w in graded) / len(graded), 3)

    llm_analysis = []
    from utils.groq_client import get_groq_key
    active_key = groq_api_key or get_groq_key()
    if uncertain and active_key and source_text and language == 'ar':
        llm_analysis = _llm_pronounce_analysis(
            uncertain, source_text, active_key, llm_model
        )

    return {
        'words':         graded,
        'uncertain':     uncertain,
        'llm_analysis':  llm_analysis,
        'overall_score': overall
    }


PRONOUNCE_PROMPT = """You are an Arabic linguistics expert for interpreter training at ETIB Beirut.

SOURCE SPEECH (expected — with full tashkeel):
{source}

STUDENT'S UNCERTAIN WORDS (low alignment confidence — likely mispronounced):
{uncertain}

For each uncertain word, analyze:
1. What is the correct tashkeel/إعراب based on its grammatical role in the source sentence?
2. What case ending error did the student likely make?
3. Brief pedagogical explanation.

Return ONLY valid JSON (no markdown):
[
  {{
    "word": "unvocalized word",
    "expected_form": "with correct tashkeel",
    "likely_error": "e.g. said فتحة instead of ضمة",
    "grammatical_role": "e.g. subject → nominative ُ",
    "explanation": "one sentence pedagogical explanation"
  }}
]
"""


def _llm_pronounce_analysis(
    uncertain_words: list,
    source_text:     str,
    groq_api_key:    str,
    llm_model:       str
) -> list:
    """Call LLM to interpret what specific tashkeel errors occurred."""
    try:
        from groq import Groq
        client  = Groq(api_key=groq_api_key)
        words_str = ', '.join(f'"{w["word"]}" (confidence {w["score"]})' for w in uncertain_words)

        prompt = PRONOUNCE_PROMPT.format(
            source=source_text,
            uncertain=words_str
        )

        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {'role': 'system', 'content':
                 'You are an Arabic linguistics expert. Return only valid JSON.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=800,
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        # strip markdown fences
        fence = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
        if fence:
            content = fence.group(1).strip()
        s, e = content.find('['), content.rfind(']') + 1
        if s >= 0 and e > s:
            content = content[s:e]
        return json.loads(content)
    except Exception as ex:
        print(f'[Alignment] LLM analysis failed: {ex}')
        return []
