"""
Module A - LLM Speech Generation.

Generates structured interpreter training material in Arabic, French, and
English. The endpoint returns a speech script plus the first training support
materials needed by the frontend: summary, MCQs, glossary, and metadata.
"""
import json
import re

from flask import Blueprint, jsonify, request

from config import DEFAULT_WPM
from services.llm_service import generate_text

module_a_bp = Blueprint('module_a', __name__)

SUPPORTED_LANGUAGES = ['ar', 'fr', 'en']

LANGUAGE_NAMES = {
    'ar': 'Arabic (Modern Standard Arabic)',
    'fr': 'French',
    'en': 'English',
}

MODE_INSTRUCTIONS = {
    'sight_translation': 'Dense written style - the text will be read visually by the trainee.',
    'consecutive': 'Natural spoken style with logical pauses every 2-3 sentences.',
    'simultaneous': 'Fast, dense delivery. Short sentences. High information density.',
}


def build_prompt(params: dict) -> str:
    topic = params.get('topic', '').strip()
    language = params.get('language', 'ar')
    target_language = params.get('target_language', 'fr')
    domain = params.get('domain', 'politics')
    word_count = params.get('word_count', 250)
    difficulty = params.get('difficulty', 'intermediate')
    structure = params.get('structure', 'well-organized')
    scenario = params.get('scenario', 'UN General Assembly')
    number_density = params.get('number_density', 'low')
    hesitations = bool(params.get('include_hesitations', False))
    mode = params.get('mode', 'consecutive')
    pressure_enabled = bool(params.get('pressure_enabled', False))
    speed_pressure = params.get('speed_pressure', 'normal')
    topic_shifts = params.get('topic_shifts', 'none')
    context_noise = bool(params.get('context_noise', False))
    cognitive_load = params.get('cognitive_load', 'medium')

    pressure_block = 'Disabled'
    if pressure_enabled:
        pressure_block = f"""Enabled
- Speaking speed cues: {speed_pressure}
- Topic shifts: {topic_shifts}
- Background/context noise: {context_noise}
- Cognitive load: {cognitive_load}
- Apply pressure through denser information, realistic time pressure, numerical load, and less predictable flow."""

    prompt = f"""Generate interpreter training material as strict JSON.

Parameters:
- Topic: {topic}
- Source/speech language: {LANGUAGE_NAMES.get(language, 'English')}
- Interpretation target language: {LANGUAGE_NAMES.get(target_language, 'French')}
- Domain: {domain}
- Target length: {word_count} words
- Difficulty: {difficulty}
- Discourse structure: {structure}
- Scenario: {scenario}
- Numbers/statistics density: {number_density}
- Interpretation mode: {mode} - {MODE_INSTRUCTIONS.get(mode, '')}
- Include simulated hesitations: {hesitations}
- Pressure simulator: {pressure_block}

Rules:
- Output ONLY valid JSON. No markdown, no code block, no preamble.
- The script must be in the source/speech language.
- The summary must be in the source/speech language.
- MCQ questions must be in the source/speech language.
- Do not translate the script into the target language.
- The target language defines the student's interpretation direction.
- The glossary must include important terms in all three languages: Arabic, French, and English.
- Write exactly as a speaker would deliver the script at a real {scenario}.
- Match the rhetorical register of that scenario.
- Return 3 MCQs and 8 to 12 glossary terms.
- Use this exact JSON shape:
{{
  "script": "string",
  "summary": "string",
  "mcqs": [
    {{
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "answer": "string"
    }}
  ],
  "glossary": [
    {{
      "term": "string",
      "arabic": "string",
      "french": "string",
      "english": "string",
      "definition": "string"
    }}
  ],
  "metadata": {{
    "pressure_enabled": {str(pressure_enabled).lower()},
    "pressure_factors": ["string"]
  }}
}}
"""

    if language == 'ar':
        prompt += """
Arabic requirements:
- Write entirely in Modern Standard Arabic. Do not use dialect.
- Do not use English or French terms when Arabic equivalents exist.
- Maintain a formal conference register throughout.
"""

    if hesitations:
        fillers = {
            'ar': 'آ، إ، أقصد، أي',
            'fr': "euh, c'est-à-dire, en fait",
            'en': 'um, uh, I mean, you know',
        }.get(language, '')
        prompt += f"\n- Include natural hesitation markers: {fillers}"

    return prompt


def parse_generation_output(raw_output: str) -> dict:
    """Parse model JSON and fall back to treating the output as script text."""
    text = raw_output.strip()
    data = None

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                data = None

    if not isinstance(data, dict):
        data = {'script': text}

    return {
        'script': str(data.get('script', '')).strip(),
        'summary': str(data.get('summary', '')).strip(),
        'mcqs': data.get('mcqs') if isinstance(data.get('mcqs'), list) else [],
        'glossary': data.get('glossary') if isinstance(data.get('glossary'), list) else [],
        'metadata': data.get('metadata') if isinstance(data.get('metadata'), dict) else {},
    }


def validate_params(params: dict) -> tuple[dict, int] | tuple[None, None]:
    if params.get('language') not in [*SUPPORTED_LANGUAGES, None]:
        return {'error': "language must be 'ar', 'fr', or 'en'"}, 400

    if params.get('target_language') not in [*SUPPORTED_LANGUAGES, None]:
        return {'error': "target_language must be 'ar', 'fr', or 'en'"}, 400

    topic = str(params.get('topic', '')).strip()
    if not topic:
        return {'error': 'topic is required'}, 400

    try:
        word_count = int(params.get('word_count', 250))
    except (TypeError, ValueError):
        return {'error': 'word_count must be a number'}, 400

    if word_count < 50 or word_count > 800:
        return {'error': 'word_count must be between 50 and 800'}, 400

    return None, None


@module_a_bp.route('/generate', methods=['POST'])
def generate_speech():
    params = request.get_json()
    if not params:
        return jsonify({'error': 'Request body must be JSON'}), 400

    validation_error, status = validate_params(params)
    if validation_error:
        return jsonify(validation_error), status

    try:
        prompt = build_prompt(params)
        raw_output = generate_text(
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are an expert speech writer and interpreter trainer. '
                        'Return only valid JSON in the requested schema.'
                    ),
                },
                {'role': 'user', 'content': prompt},
            ],
            max_tokens=2600,
            temperature=0.7,
        )
        generated = parse_generation_output(raw_output)
        script = generated['script']
        word_count = len(script.split())
        wpm = params.get('wpm', DEFAULT_WPM)

        return jsonify({
            'script': script,
            'summary': generated['summary'],
            'mcqs': generated['mcqs'],
            'glossary': generated['glossary'],
            'metadata': {
                **generated['metadata'],
                'topic': params.get('topic', '').strip(),
                'pressure_enabled': bool(params.get('pressure_enabled', False)),
                'pressure_settings': {
                    'speed_pressure': params.get('speed_pressure', 'normal'),
                    'topic_shifts': params.get('topic_shifts', 'none'),
                    'context_noise': bool(params.get('context_noise', False)),
                    'cognitive_load': params.get('cognitive_load', 'medium'),
                },
            },
            'word_count': word_count,
            'estimated_duration_seconds': round((word_count / wpm) * 60),
            'language': params.get('language', 'ar'),
            'target_language': params.get('target_language', 'fr'),
            'topic': params.get('topic', '').strip(),
            'domain': params.get('domain', 'politics'),
            'params_used': params,
        })

    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@module_a_bp.route('/from-document', methods=['POST'])
def generate_from_document():
    return jsonify({'status': 'not yet implemented - planned for Week 2'}), 501
