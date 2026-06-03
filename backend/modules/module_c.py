"""
Module C — ASR Transcription
==============================
Source: Cahier des charges, Section C — Module d'évaluation automatisée (recording part)

Responsible: Person 5

Accepts a student's recorded interpretation audio and:
  C1  Transcribes it using Whisper (faster-whisper, local, free)
  C2  Returns word-level timestamps (critical for Module D error detection)
  C3  Detects and flags silences automatically via VAD

Note from cahier des charges:
  "Des outils existent mais ils ne sont pas encore performants notamment pour l'arabe"
  → Document all Arabic quality issues in docs/asr_evaluation.md

Endpoints:
  POST /api/module-c/transcribe   — transcribe an uploaded audio file
  GET  /api/module-c/status       — check if Whisper model is loaded
"""
import os
import uuid
from flask import Blueprint, request, jsonify
from config import (WHISPER_MODEL_SIZE, WHISPER_DEVICE,
                    WHISPER_COMPUTE_TYPE, UPLOAD_FOLDER)

module_c_bp = Blueprint('module_c', __name__)

# Model is loaded once at first use, then cached — loading takes ~10 seconds
_whisper_model = None

def get_whisper_model():
    """Load and cache the Whisper model. Called on first transcription request."""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        print(f'[Module C] Loading Whisper {WHISPER_MODEL_SIZE} model...')
        _whisper_model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE
        )
        print('[Module C] Whisper model ready.')
    return _whisper_model


def transcribe_audio(audio_path: str, language: str = 'ar') -> dict:
    """
    Transcribe an audio file. Returns full transcript + word-level timestamps.

    The word timestamps are essential for Module D:
      - Gaps between segments → long silences / omissions
      - Low probability words → hesitations / mumbling
      - Repeated words → repetitions
    """
    model = get_whisper_model()

    segments_iter, info = model.transcribe(
        audio_path,
        language=language,
        task='transcribe',       # keep original language (don't translate)
        word_timestamps=True,    # REQUIRED for Module D
        vad_filter=True,         # remove non-speech regions
        vad_parameters={
            'min_silence_duration_ms': 500  # gaps > 500ms are recorded
        }
    )

    full_text = ''
    all_segments = []

    for seg in segments_iter:
        seg_data = {
            'start': round(seg.start, 2),
            'end': round(seg.end, 2),
            'text': seg.text.strip(),
            'words': []
        }
        if seg.words:
            for w in seg.words:
                seg_data['words'].append({
                    'word': w.word,
                    'start': round(w.start, 2),
                    'end': round(w.end, 2),
                    'probability': round(w.probability, 3)
                })
        all_segments.append(seg_data)
        full_text += seg.text + ' '

    return {
        'full_text': full_text.strip(),
        'language_detected': info.language,
        'language_confidence': round(info.language_probability, 3),
        'duration_seconds': round(info.duration, 1),
        'segments': all_segments
    }


@module_c_bp.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Transcribe a student's recorded interpretation.

    Request: multipart/form-data
      audio     file   audio file (MP3, WAV, M4A, OGG)
      language  str    expected language: 'ar'|'fr'|'en'    default 'ar'

    Response (JSON):
      full_text           str   complete transcript
      language_detected   str   language Whisper detected
      language_confidence float
      duration_seconds    float audio duration
      segments            list  [ { start, end, text, words: [{word, start, end, probability}] } ]
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided. Send as multipart/form-data with key "audio"'}), 400

    audio_file = request.files['audio']
    language = request.form.get('language', 'ar')

    # Save uploaded file temporarily
    ext = os.path.splitext(audio_file.filename)[1] or '.mp3'
    temp_filename = f'upload_{uuid.uuid4().hex[:8]}{ext}'
    temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
    audio_file.save(temp_path)

    try:
        result = transcribe_audio(temp_path, language)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@module_c_bp.route('/status')
def model_status():
    """Check if the Whisper model is loaded and ready."""
    return jsonify({
        'model_loaded': _whisper_model is not None,
        'model_size': WHISPER_MODEL_SIZE,
        'device': WHISPER_DEVICE
    })
