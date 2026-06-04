"""
Module A — LLM Speech Generation
==================================
Source: Cahier des charges, Section A — Génération automatique de discours

Responsible: Person 2

Generates parametric training speeches in Arabic, French, and English
using free LLM APIs (Groq primary, Google AI Studio fallback, Ollama offline).

Endpoints:
  POST /api/module-a/generate       — generate a speech from parameters
  POST /api/module-a/from-document  — generate a speech from uploaded document (TODO)
"""
import os
from flask import Blueprint, request, jsonify
from groq import Groq
from config import GROQ_API_KEY, PRIMARY_LLM_MODEL, DEFAULT_WPM

module_a_bp = Blueprint('module_a', __name__)
client = None


def get_groq_client():
    """Create the Groq client only when Module A generation is called."""
    global client
    if not GROQ_API_KEY:
        raise RuntimeError('GROQ_API_KEY is not configured')
    if client is None:
        client = Groq(api_key=GROQ_API_KEY)
    return client

LANGUAGE_NAMES = {
    'ar': 'Arabic (Modern Standard Arabic / الفصحى)',
    'fr': 'French',
    'en': 'English'
}

def build_prompt(params: dict) -> str:
    """
    Build the LLM prompt from user-supplied parameters.
    Every parameter maps directly to a requirement in the cahier des charges Section A.
    """
    language     = params.get('language', 'ar')
    domain       = params.get('domain', 'politics')
    word_count   = params.get('word_count', 250)
    difficulty   = params.get('difficulty', 'intermediate')
    structure    = params.get('structure', 'well-organized')
    scenario     = params.get('scenario', 'UN General Assembly')
    num_density  = params.get('number_density', 'low')
    hesitations  = params.get('include_hesitations', False)
    mode         = params.get('mode', 'consecutive')  # sight_translation / consecutive / simultaneous

    mode_instructions = {
        'sight_translation': 'Dense written style — the text will be read visually by the trainee.',
        'consecutive':       'Natural spoken style with logical pauses every 2-3 sentences.',
        'simultaneous':      'Fast, dense delivery. Short sentences. High information density.',
    }

    prompt = f"""Generate a {LANGUAGE_NAMES.get(language, 'English')} conference speech for interpreter training.

Parameters:
- Domain: {domain}
- Target length: {word_count} words
- Difficulty: {difficulty}
- Discourse structure: {structure}
- Scenario: {scenario}
- Numbers/statistics density: {num_density}
- Interpretation mode: {mode} — {mode_instructions.get(mode, '')}
- Include simulated hesitations: {hesitations}

Rules:
- Output ONLY the speech text. No title, no labels, no preamble, no explanation.
- Write exactly as a speaker would deliver it at a real {scenario}.
- Match the rhetorical register of that scenario precisely.
"""

    if language == 'ar':
        prompt += """
ARABIC REQUIREMENTS — strictly follow these:
- Write entirely in Modern Standard Arabic (الفصحى). No dialect words.
- Use authentic Arabic oratory connectors: أيها السادة، إن، وعليه، وفي هذا الإطار، ومما لا شك فيه...
- Do NOT use English or French terms when Arabic equivalents exist.
- Numbers may be written as Arabic-Indic numerals (٢٠٢٤) or Eastern Arabic numerals.
- Maintain formal conference register throughout.
- Diacritics (تشكيل) are optional but welcome on difficult words.
"""

    if hesitations:
        ar_hesitations = 'آ، إ، أقصد، أي' if language == 'ar' else ''
        fr_hesitations = 'euh, c\'est-à-dire, en fait' if language == 'fr' else ''
        en_hesitations = 'um, uh, I mean, you know' if language == 'en' else ''
        fillers = ar_hesitations or fr_hesitations or en_hesitations
        prompt += f"\n- Include natural hesitation markers: {fillers}"

    return prompt


@module_a_bp.route('/generate', methods=['POST'])
def generate_speech():
    """
    Generate a parametric training speech.

    Request body (JSON):
      language         str   'ar' | 'fr' | 'en'              required
      domain           str   e.g. 'climate', 'diplomacy'     required
      word_count       int   50–800                           default 250
      difficulty       str   'beginner'|'intermediate'|'advanced'
      structure        str   'well-organized'|'semi-structured'|'deliberately disorganized'
      scenario         str   e.g. 'UN General Assembly'
      number_density   str   'low'|'medium'|'high'
      include_hesitations bool
      mode             str   'sight_translation'|'consecutive'|'simultaneous'
      wpm              int   words per minute (for duration estimate)

    Response (JSON):
      script                    str   the generated speech text
      word_count                int
      estimated_duration_seconds int
      language                  str
      domain                    str
      params_used               dict
    """
    params = request.get_json()
    if not params:
        return jsonify({'error': 'Request body must be JSON'}), 400

    if params.get('language') not in ['ar', 'fr', 'en', None]:
        return jsonify({'error': "language must be 'ar', 'fr', or 'en'"}), 400

    try:
        prompt = build_prompt(params)

        response = get_groq_client().chat.completions.create(
            model=PRIMARY_LLM_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are an expert speech writer for international conference '
                        'interpreter training. You produce authentic, high-quality speeches '
                        'in the requested language. You follow instructions precisely.'
                    )
                },
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=1800,
            temperature=0.7
        )

        script = response.choices[0].message.content.strip()
        word_count = len(script.split())
        wpm = params.get('wpm', DEFAULT_WPM)

        return jsonify({
            'script': script,
            'word_count': word_count,
            'estimated_duration_seconds': round((word_count / wpm) * 60),
            'language': params.get('language', 'ar'),
            'domain': params.get('domain', 'politics'),
            'params_used': params
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@module_a_bp.route('/from-document', methods=['POST'])
def generate_from_document():
    """
    Generate a speech based on an uploaded document (PDF, DOCX).
    Requirement: Cahier des charges Section A — document upload.
    TODO: Person 2 — implement in Week 2.
    """
    return jsonify({'status': 'not yet implemented — planned for Week 2'}), 501
