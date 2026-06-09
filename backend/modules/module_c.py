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
import uuid
import json
from flask import Blueprint, request, jsonify
from config import (GROQ_API_KEY, WHISPER_MODEL_SIZE, WHISPER_DEVICE,
                    WHISPER_COMPUTE_TYPE, UPLOAD_FOLDER)

module_c_bp = Blueprint('module_c', __name__)

_whisper_model = None


# ── Groq hosted Whisper (fast) ───────────────────────────────────────────────

def _transcribe_groq(audio_path: str, language: str) -> dict:
    """Transcribe via Groq's hosted whisper-large-v3. Returns in seconds."""
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)

    with open(audio_path, 'rb') as f:
        result = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f),
            model='whisper-large-v3',
            language=language,
            response_format='verbose_json'
        )

    segments = []
    raw_segs = getattr(result, 'segments', None) or []
    for seg in raw_segs:
        if isinstance(seg, dict):
            segments.append({
                'start': round(seg.get('start', 0), 2),
                'end':   round(seg.get('end', 0), 2),
                'text':  seg.get('text', '').strip(),
                'words': []
            })
        else:
            segments.append({
                'start': round(getattr(seg, 'start', 0), 2),
                'end':   round(getattr(seg, 'end', 0), 2),
                'text':  getattr(seg, 'text', '').strip(),
                'words': []
            })

    return {
        'full_text':           result.text.strip(),
        'language_detected':   language,
        'language_confidence': 1.0,
        'duration_seconds':    round(getattr(result, 'duration', 0) or 0, 1),
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
        word_timestamps=True, vad_filter=True,
        vad_parameters={'min_silence_duration_ms': 500},
        suppress_tokens=[],          # output raw tokens — prevents Arabic grammar normalization
        condition_on_previous_text=False,  # prevents drift toward "corrected" Arabic across segments
    )
    full_text = ''
    all_segments = []
    for seg in segments_iter:
        seg_data = {
            'start': round(seg.start, 2), 'end': round(seg.end, 2),
            'text': seg.text.strip(), 'words': []
        }
        for w in (seg.words or []):
            seg_data['words'].append({
                'word': w.word, 'start': round(w.start, 2),
                'end': round(w.end, 2), 'probability': round(w.probability, 3)
            })
        all_segments.append(seg_data)
        full_text += seg.text + ' '
    return {
        'full_text': full_text.strip(),
        'language_detected': info.language,
        'language_confidence': round(info.language_probability, 3),
        'duration_seconds': round(info.duration, 1),
        'segments': all_segments,
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
    if not GROQ_API_KEY or not student_text.strip():
        return student_text
    try:
        from groq import Groq
        from config import PRIMARY_LLM_MODEL
        client = Groq(api_key=GROQ_API_KEY)

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

    ext = os.path.splitext(audio_file.filename)[1] or '.webm'
    temp_path = os.path.join(UPLOAD_FOLDER, f'upload_{uuid.uuid4().hex[:8]}{ext}')
    audio_file.save(temp_path)

    try:
        # Try Groq first (fast), fall back to local Whisper
        if GROQ_API_KEY:
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

    ext       = os.path.splitext(audio_file.filename)[1] or '.webm'
    temp_path = os.path.join(UPLOAD_FOLDER, f'align_{uuid.uuid4().hex[:8]}{ext}')
    audio_file.save(temp_path)

    try:
        from modules.alignment import align_words, extract_word_scores, compare_against_source
        from config import GROQ_API_KEY, PRIMARY_LLM_MODEL

        # Step 1: WhisperX forced alignment (or fall back to Whisper scores)
        aligned_segs  = align_words(temp_path, segments)
        whisperx_used = aligned_segs is not segments  # True if WhisperX ran

        # Step 2: extract flat word list with scores
        word_scores = extract_word_scores(aligned_segs)

        # Step 3: compare against source + LLM analysis
        result = compare_against_source(
            word_scores, source_text, language,
            GROQ_API_KEY, PRIMARY_LLM_MODEL
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
    return jsonify({
        'groq_available':  bool(GROQ_API_KEY),
        'local_loaded':    _whisper_model is not None,
        'model_size':      WHISPER_MODEL_SIZE,
        'primary_method':  'groq' if GROQ_API_KEY else 'local'
    })
