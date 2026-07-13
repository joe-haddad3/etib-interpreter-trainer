"""
Module C — ASR Transcription
==============================
Primary:  Groq hosted Whisper-large-v3 (fast, ~3 sec, requires GROQ_API_KEY)
Fallback: faster-whisper local model   (slow, ~1-3 min, no key needed)

Endpoints:
  POST /api/module-c/transcribe   — transcribe an uploaded audio file
  GET  /api/module-c/status       — check transcription method available
"""
import os
import re
import uuid
import json
from flask import Blueprint, request, jsonify
from config import (GROQ_API_KEY, WHISPER_MODEL_SIZE, WHISPER_DEVICE,
                    WHISPER_COMPUTE_TYPE, UPLOAD_FOLDER)

module_c_bp = Blueprint('module_c', __name__)

_ALLOWED_AUDIO_EXTS = {'.mp3', '.wav', '.m4a', '.ogg', '.webm', '.flac', '.mp4', '.mpeg', '.mpga', '.opus'}

def _clean_asr_text(text: str) -> str:
    """Strip ASR artifacts: ellipsis tokens Groq/Whisper inserts for silent or unclear audio."""
    cleaned = str(text or '').strip()
    cleaned = re.sub(r'\.{2,}', '', cleaned)   # remove all ... regardless of position
    cleaned = re.sub(r'…', '', cleaned)          # remove unicode ellipsis
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)   # collapse extra spaces left behind
    return cleaned.strip()


def _safe_audio_ext(filename: str) -> str:
    """Return a whitelisted audio extension from an untrusted filename."""
    import os as _os
    ext = _os.path.splitext(_os.path.basename(str(filename or '')))[1].lower()
    return ext if ext in _ALLOWED_AUDIO_EXTS else '.webm'


_whisper_model = None

# Priming prompts containing disfluencies — Whisper imitates the style of the
# initial prompt, making it far more likely to transcribe "euh"/"um"/"يعني"
# verbatim instead of silently cleaning them out of the transcript.
DISFLUENCY_PROMPTS = {
    'ar': 'إممم، آه، يعني، أقصد... طيب، يعني كيف أقول هاد الشي.',
    'fr': "Euh, alors, ben, c'est-à-dire... voilà, donc, euh, comment dire.",
    'en': "Um, well, uh, like, you know... so, I mean, er, how do I put this.",
}


# ── Groq hosted Whisper (fast) ───────────────────────────────────────────────

_VERBATIM_EXAMPLES = {
    'fr': "Transcription verbatim. Garder les mots répétés: 'climat climat action' → 'climat climat action'.",
    'ar': "نسخ حرفي. الإبقاء على الكلمات المكررة كما هي.",
    'en': "Transcribe verbatim. Keep repeated words: 'climate climate action' → 'climate climate action'.",
}

def _transcribe_groq(audio_path: str, language: str) -> dict:
    """Transcribe via Groq REST API with word-level timestamps to preserve repetitions."""
    import requests as _requests
    from utils.groq_client import get_groq_key
    key = get_groq_key()
    if not key:
        raise RuntimeError('No Groq API key')

    # Combine disfluency prompt + verbatim instruction so repeated words survive
    disfluency = DISFLUENCY_PROMPTS.get(language, DISFLUENCY_PROMPTS['en'])
    verbatim   = _VERBATIM_EXAMPLES.get(language, _VERBATIM_EXAMPLES['en'])
    prompt     = f"{disfluency} {verbatim}"

    with open(audio_path, 'rb') as fh:
        resp = _requests.post(
            'https://api.groq.com/openai/v1/audio/transcriptions',
            headers={'Authorization': f'Bearer {key}'},
            files={'file': (os.path.basename(audio_path), fh)},
            data=[
                ('model',                      'whisper-large-v3'),
                ('language',                   language),
                ('response_format',            'verbose_json'),
                ('timestamp_granularities[]',  'word'),
                ('timestamp_granularities[]',  'segment'),
                ('prompt',                     prompt[:400]),
            ],
            timeout=120,
        )
    if not resp.ok:
        raise RuntimeError(f'Groq transcription failed: {resp.status_code} {resp.text[:120]}')

    data       = resp.json()
    raw_segs   = data.get('segments') or []
    raw_words  = data.get('words') or []

    # Build segments from segment-level data (used for silence/timing analysis)
    segments = []
    for seg in raw_segs:
        seg_text = _clean_asr_text(str(seg.get('text', '')).strip())
        if not seg_text:
            continue
        segments.append({
            'start': round(float(seg.get('start', 0) or 0), 2),
            'end':   round(float(seg.get('end', 0) or 0), 2),
            'text':  seg_text,
            'words': [],
        })

    # Attach word-level timestamps so repetition detection has per-word timing
    for w in raw_words:
        token = _clean_asr_text(str(w.get('word', '')).strip())
        if not token:
            continue
        start = round(float(w.get('start', 0) or 0), 2)
        end   = round(float(w.get('end', 0) or 0), 2)
        entry = {'word': token, 'start': start, 'end': end, 'probability': 1.0}
        for seg in segments:
            if seg['start'] - 0.05 <= start < seg['end'] + 0.05:
                seg['words'].append(entry)
                break
        else:
            if segments:
                segments[-1]['words'].append(entry)

    # Build full_text from word timestamps — preserves repetitions Groq keeps
    word_tokens = [w.get('word', '') for seg in segments for w in seg.get('words', [])]
    clean_text  = re.sub(r'\s{2,}', ' ', ' '.join(word_tokens)).strip() if word_tokens \
                  else _clean_asr_text(str(data.get('text', '')))

    return {
        'full_text':           clean_text,
        'no_speech_detected':  not bool(clean_text),
        'language_detected':   str(data.get('language', language) or language),
        'language_confidence': 1.0,
        'duration_seconds':    round(float(data.get('duration', 0) or 0), 1),
        'segments':            segments,
        'method':              'groq'
    }


# ── Local faster-whisper (fallback) ─────────────────────────────────────────

def _get_local_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        print(f'[Module C] Loading local Whisper {WHISPER_MODEL_SIZE}...')
        _whisper_model = WhisperModel(
            WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE
        )
        print('[Module C] Local Whisper ready.')
    return _whisper_model


def _transcribe_local(audio_path: str, language: str) -> dict:
    """Transcribe with local faster-whisper. Slow on CPU but always available."""
    model = _get_local_model()
    segments_iter, info = model.transcribe(
        audio_path, language=language, task='transcribe',
        word_timestamps=True,
        vad_filter=False,               # disabled: preserves silence gaps for timestamp accuracy
        suppress_tokens=[],             # output raw tokens — prevents Arabic grammar normalization
        condition_on_previous_text=False,   # prevents drift toward "corrected" Arabic
        compression_ratio_threshold=100.0,  # disable repetition-based fallback (keeps repeated words)
        log_prob_threshold=-100.0,          # disable low-confidence fallback (keeps hesitations)
        temperature=0.0,                    # greedy decoding — no temperature sampling
        beam_size=1,                        # greedy: no beam search collapse of repetitions
        initial_prompt=DISFLUENCY_PROMPTS.get(language, DISFLUENCY_PROMPTS['en']),  # primes Whisper to keep "euh/um" fillers
    )
    full_text = ''
    all_segments = []
    for seg in segments_iter:
        # Skip non-speech annotations Whisper sometimes hallucinates over
        # noisy/silent audio, e.g. "[Bruit de fond]", "[Music]" — not real words.
        seg_text = seg.text.strip()
        if not seg_text or seg_text[0] in '[(':
            continue
        seg_data = {
            'start': round(seg.start, 2), 'end': round(seg.end, 2),
            'text': seg_text, 'words': []
        }
        for w in (seg.words or []):
            seg_data['words'].append({
                'word': w.word, 'start': round(w.start, 2),
                'end': round(w.end, 2), 'probability': round(w.probability, 3)
            })
        all_segments.append(seg_data)
        full_text += seg.text + ' '
    clean_text = _clean_asr_text(full_text)
    return {
        'full_text':           clean_text,
        'no_speech_detected':  not bool(clean_text),
        'language_detected':   info.language,
        'language_confidence': round(info.language_probability, 3),
        'duration_seconds':    round(info.duration, 1),
        'segments':            all_segments,
        'method': 'local'
    }


# ── Arabic tashkeel post-processing ─────────────────────────────────────────

def _add_tashkeel(student_text: str, source_text: str = '') -> str:
    """
    Add tashkeel that reflects what the STUDENT actually said — including their errors.
    If source_text is provided, the LLM uses it as a reference to detect deviations
    and mark the student's actual pronunciation (wrong case endings, wrong vowels, etc.)
    Returns original text if tashkeel fails (never raises).
    """
    if not student_text.strip():
        return student_text
    try:
        from utils.groq_client import get_groq_client, get_groq_key
        from config import PRIMARY_LLM_MODEL
        if not get_groq_key():
            return student_text
        client = get_groq_client()

        if source_text.strip():
            user_prompt = f"""You are an Arabic phonetics expert for interpreter training at ETIB Beirut.

ORIGINAL SOURCE SPEECH (correct Arabic reference):
{source_text}

STUDENT TRANSCRIPT (what the student actually said):
{student_text}

Your task:
1. Add tashkeel to the STUDENT TRANSCRIPT that reflects what the student actually pronounced.
2. Do NOT correct the student's errors — if they used the wrong case ending (e.g. فتحة instead of ضمة), write the wrong diacritic.
3. Compare with the source speech: where the student deviated, mark what they likely said.
4. Return ONLY the student's text with tashkeel. Nothing else."""
        else:
            user_prompt = f"""You are an Arabic phonetics expert. Add tashkeel to this student speech transcript.

Rules:
- Add diacritics that reflect what was ACTUALLY spoken, not what is grammatically correct.
- Do NOT fix case endings or grammar errors — preserve them exactly as spoken.
- Use natural spoken Arabic patterns, not formal written Arabic.
- Return ONLY the vocalized text, nothing else.

Student transcript:
{student_text}"""

        response = client.chat.completions.create(
            model=PRIMARY_LLM_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are an Arabic phonetics expert for interpreter training. '
                        'You add tashkeel that reflects the student\'s actual pronunciation including errors. '
                        'Never correct the student\'s mistakes in the tashkeel. Return only vocalized text.'
                    )
                },
                {'role': 'user', 'content': user_prompt}
            ],
            max_tokens=max(500, len(student_text) * 3),
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f'[Module C] Tashkeel failed: {e}')
        return student_text


# ── Endpoints ────────────────────────────────────────────────────────────────

@module_c_bp.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Transcribe a student's recorded interpretation.

    Request: multipart/form-data
      audio     file   MP3, WAV, M4A, OGG, WEBM
      language  str    'ar' | 'fr' | 'en'   default 'ar'
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file. Send multipart/form-data with key "audio"'}), 400

    audio_file  = request.files['audio']
    language    = request.form.get('language', 'ar')
    source_text = request.form.get('source_text', '')  # optional — source speech for error comparison

    ext = _safe_audio_ext(audio_file.filename)
    temp_path = os.path.join(UPLOAD_FOLDER, f'upload_{uuid.uuid4().hex[:8]}{ext}')
    audio_file.save(temp_path)

    try:
        # Try Groq first (fast), fall back to local Whisper
        from utils.groq_client import get_groq_key
        if get_groq_key():
            try:
                result = _transcribe_groq(temp_path, language)
            except Exception as groq_err:
                print(f'[Module C] Groq failed ({groq_err}), falling back to local Whisper')
                result = _transcribe_local(temp_path, language)
        else:
            result = _transcribe_local(temp_path, language)

        # For Arabic: add tashkeel reflecting what the student actually said
        if language == 'ar' and result.get('full_text'):
            result['vocalized_text'] = _add_tashkeel(result['full_text'], source_text)

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@module_c_bp.route('/align', methods=['POST'])
def align_pronunciation():
    """
    Forced alignment + pronunciation assessment.
    Aligns the student's transcript to their audio using WAV2VEC2-XLSR-Arabic,
    then compares uncertain words against the vocalized source speech.

    Request: multipart/form-data
      audio         file   student's audio (same file as /transcribe)
      segments      str    JSON — Whisper segments from previous /transcribe call
      source_text   str    vocalized source speech (AR only)
      language      str    'ar' | 'fr' | 'en'   default 'ar'

    Response (JSON):
      words         list  [{word, start, end, score, grade}]
      uncertain     list  low-confidence words
      llm_analysis  list  [{word, expected_form, likely_error, explanation}]
      overall_score float pronunciation confidence 0–1
      whisperx_used bool
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file  = request.files['audio']
    language    = request.form.get('language', 'ar')
    source_text = request.form.get('source_text', '')
    segments_raw = request.form.get('segments', '[]')

    try:
        segments = json.loads(segments_raw)
    except Exception:
        segments = []

    ext       = _safe_audio_ext(audio_file.filename)
    temp_path = os.path.join(UPLOAD_FOLDER, f'align_{uuid.uuid4().hex[:8]}{ext}')
    audio_file.save(temp_path)

    try:
        from modules.alignment import align_words, extract_word_scores, compare_against_source
        from config import PRIMARY_LLM_MODEL

        # Step 1: WhisperX forced alignment (or fall back to Whisper scores)
        aligned_segs  = align_words(temp_path, segments)
        whisperx_used = aligned_segs is not segments  # True if WhisperX ran

        # Step 2: extract flat word list with scores
        word_scores = extract_word_scores(aligned_segs)

        # Step 3: compare against source + LLM analysis (key comes from flask.g via groq_client)
        result = compare_against_source(
            word_scores, source_text, language,
            None, PRIMARY_LLM_MODEL
        )
        result['whisperx_used'] = whisperx_used
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@module_c_bp.route('/status')
def model_status():
    from utils.groq_client import get_groq_key
    has_key = bool(get_groq_key())
    return jsonify({
        'groq_available':  has_key,
        'local_loaded':    _whisper_model is not None,
        'model_size':      WHISPER_MODEL_SIZE,
        'primary_method':  'groq' if has_key else 'local'
    })
