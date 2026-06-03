"""
Module B — TTS + Pedagogical Materials
========================================
Source: Cahier des charges, Section B — Production automatique associée au discours

Responsible: Person 4

For every generated speech, this module produces:
  B1  Audio (TTS) with configurable voice and rate
  B2  Accent variability (AR: Lebanese, Gulf, Egyptian; FR: Paris, Canadian; EN: US, UK, AU)
  B3  Full text script
  B4  Key terms list
  B5  Preparatory context / mind map (text-based)
  B6  Comprehension questions
  B7  Flashcards (term → definition, term → equivalent)
  B8  Thematic summary
  B9  MCQ (multiple-choice questions)
  B10 Key concepts identification
  B11 Editable trilingual glossary AR-FR-EN (downloadable)
  B12 Sight translation scroller interface (served by frontend)

Endpoints:
  POST /api/module-b/tts             — convert text to speech audio
  POST /api/module-b/materials       — generate all pedagogical materials for a speech
  GET  /api/module-b/audio/<filename> — serve generated audio file
"""
import os
import asyncio
import uuid
from flask import Blueprint, request, jsonify, send_file
from config import TTS_VOICES, DEFAULT_VOICE, AUDIO_OUTPUT_FOLDER, GROQ_API_KEY, PRIMARY_LLM_MODEL

module_b_bp = Blueprint('module_b', __name__)


# ── TTS ─────────────────────────────────────────────────────────────────────

def get_voice(language: str, accent: str = None) -> str:
    """Return the edge-tts voice name for a given language and accent."""
    lang_voices = TTS_VOICES.get(language, TTS_VOICES['en'])
    if accent and accent in lang_voices:
        return lang_voices[accent]
    return DEFAULT_VOICE.get(language, DEFAULT_VOICE['en'])

async def _tts_async(text: str, voice: str, output_path: str, rate: str = '+0%'):
    """Internal async TTS call using edge-tts."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)

def run_tts(text: str, language: str, accent: str = None,
            rate_adjustment: int = 0) -> str:
    """
    Convert text to speech. Returns path to the generated MP3 file.
    rate_adjustment: percentage change from normal speed (-50 to +50)
    """
    voice = get_voice(language, accent)
    rate_str = f'{rate_adjustment:+d}%' if rate_adjustment != 0 else '+0%'
    filename = f'speech_{uuid.uuid4().hex[:8]}.mp3'
    output_path = os.path.join(AUDIO_OUTPUT_FOLDER, filename)
    asyncio.run(_tts_async(text, voice, output_path, rate_str))
    return output_path, filename


@module_b_bp.route('/tts', methods=['POST'])
def text_to_speech():
    """
    Convert a speech script to audio.

    Request body (JSON):
      text             str   the speech text                  required
      language         str   'ar' | 'fr' | 'en'              required
      accent           str   e.g. 'LB', 'EG', 'US', 'GB'    optional
      rate_adjustment  int   -50 (slower) to +50 (faster)    default 0

    Response (JSON):
      audio_url   str   URL to retrieve the audio file
      filename    str   filename for reference
      voice_used  str   the edge-tts voice name
    """
    params = request.get_json()
    if not params or not params.get('text'):
        return jsonify({'error': 'text is required'}), 400

    try:
        path, filename = run_tts(
            text=params['text'],
            language=params.get('language', 'ar'),
            accent=params.get('accent'),
            rate_adjustment=params.get('rate_adjustment', 0)
        )
        return jsonify({
            'audio_url': f'/api/module-b/audio/{filename}',
            'filename': filename,
            'voice_used': get_voice(params.get('language', 'ar'), params.get('accent'))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@module_b_bp.route('/audio/<filename>')
def serve_audio(filename: str):
    """Serve a generated audio file."""
    path = os.path.join(AUDIO_OUTPUT_FOLDER, filename)
    if not os.path.exists(path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(path, mimetype='audio/mpeg')


# ── Pedagogical materials ────────────────────────────────────────────────────

@module_b_bp.route('/materials', methods=['POST'])
def generate_materials():
    """
    Generate all pedagogical materials for a given speech script.
    Calls the LLM once with a structured prompt to get everything in one shot.

    Request body (JSON):
      script     str   the speech text
      language   str   speech language ('ar'|'fr'|'en')
      domain     str   speech domain

    Response (JSON):
      key_terms       list
      summary         str
      mcq             list of { question, options: [A,B,C,D], answer }
      comprehension   list of str (open questions)
      flashcards      list of { term, definition, ar, fr, en }
      glossary        list of { term, ar, fr, en }

    TODO: Person 4 — implement in Week 2.
    """
    return jsonify({'status': 'not yet implemented — planned for Week 2'}), 501


@module_b_bp.route('/glossary/download', methods=['POST'])
def download_glossary():
    """
    Generate and download a trilingual glossary as a DOCX file.
    Requirement: Cahier des charges B11 — editable and downloadable.
    TODO: Person 4 — implement in Week 2.
    """
    return jsonify({'status': 'not yet implemented — planned for Week 2'}), 501
