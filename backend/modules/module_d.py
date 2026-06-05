"""
Module D — AI Evaluation + Adaptive Feedback
==============================================
Source: Cahier des charges, Section C — Module d'évaluation automatisée

Responsible: Person 5 (builds on Module C output)

Takes the transcript from Module C and the original source script from Module A,
then produces a structured error analysis and natural-language feedback report.

Error types detected (from cahier des charges):
  D1   Hesitations
  D2   Long silences / omissions
  D3   Self-corrections
  D4   Repetitions
  D5   False starts
  D6   Lapsus linguae
  D7   Number reproduction errors
  D8   Terminology problems
  D9   Arabic-specific errors (grammar, pronunciation markers)
  D10  Information loss (approximate)
  D11  Performance history tracking
  D12  Adaptive difficulty recommendations

Endpoints:
  POST /api/module-d/evaluate     — analyze transcript against source, return error report
  POST /api/module-d/feedback     — generate natural-language feedback using LLM
  GET  /api/module-d/history/<session_id> — retrieve past session results (TODO)
"""
import re
import json
from flask import Blueprint, request, jsonify
from config import GROQ_API_KEY, PRIMARY_LLM_MODEL


def _extract_json(text: str) -> dict:
    text = text.strip()
    fence = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if fence:
        text = fence.group(1).strip()
    s, e = text.find('{'), text.rfind('}') + 1
    if s >= 0 and e > s:
        text = text[s:e]
    return json.loads(text)


LLM_ANALYSIS_PROMPT = """You are a professional interpreter training evaluator at ETIB (École de Traducteurs et d'Interprètes de Beyrouth, USJ Beirut).

Analyze this student interpretation performance and produce a detailed pedagogical report.

SOURCE SPEECH ({language}):
{source}

STUDENT INTERPRETATION TRANSCRIPT:
{transcript}

ALGORITHMIC FINDINGS (already detected):
- Long silences / omissions: {silence_count}
- Word repetitions: {repetition_count}
- Hesitation markers: {hesitation_count}
- Number reproduction errors: {number_errors}

Return ONLY a valid JSON object (no markdown, no code fences):

{{
  "overall_score": 7.5,
  "language_errors": [
    {{"text": "incorrect phrase from student speech", "explanation": "what is wrong", "correction": "correct form"}}
  ],
  "auto_corrections": [
    {{"text": "phrase that was self-corrected mid-speech"}}
  ],
  "false_starts": [
    {{"text": "incomplete utterance before restarting"}}
  ],
  "lapsus_linguae": [
    {{"text": "slip of the tongue", "likely_intended": "what student meant to say"}}
  ],
  "terminology_problems": [
    {{"source_term": "term in source speech", "student_used": "what student said instead", "correct_equivalent": "proper translation/equivalent"}}
  ],
  "information_loss": [
    {{"lost_content": "content omitted or significantly distorted", "importance": "high"}}
  ],
  "strengths": ["specific strength 1", "specific strength 2"],
  "recommendations": ["specific actionable recommendation 1", "specific actionable recommendation 2"],
  "summary": "2-3 sentence overall assessment of the interpretation."
}}

Rules:
- overall_score: float 0-10 based on accuracy, fluency, terminology, completeness
- Cite actual text from the student's transcript when possible
- For Arabic: check grammar errors, wrong case endings, terminology precision
- Empty array [] is valid when nothing found
- Be pedagogically specific and constructive
"""

module_d_bp = Blueprint('module_d', __name__)


# ── Error detection (algorithmic — no LLM calls, always free) ────────────────

def detect_long_silences(segments: list, threshold_seconds: float = 2.0) -> list:
    """
    Detect gaps between segments longer than threshold.
    These likely indicate omissions (student lost track or gave up on a section).
    """
    silences = []
    for i in range(len(segments) - 1):
        gap = segments[i + 1]['start'] - segments[i]['end']
        if gap >= threshold_seconds:
            silences.append({
                'at_seconds': round(segments[i]['end'], 1),
                'duration_seconds': round(gap, 1),
                'after_text': segments[i]['text'][-60:]
            })
    return silences


def detect_repetitions(segments: list) -> list:
    """
    Detect immediately repeated words (e.g. 'the the', 'في في').
    Simple consecutive-duplicate check on all words across all segments.
    """
    all_words = []
    for seg in segments:
        for w in seg.get('words', []):
            clean = w['word'].strip().lower()
            if clean:
                all_words.append({'word': clean, 'start': w['start']})

    repetitions = []
    for i in range(len(all_words) - 1):
        if all_words[i]['word'] == all_words[i + 1]['word']:
            repetitions.append({
                'word': all_words[i]['word'],
                'at_seconds': round(all_words[i]['start'], 1)
            })
    return repetitions


def detect_hesitation_words(segments: list, language: str = 'ar') -> list:
    """
    Detect filler / hesitation words in the transcript.
    Language-specific filler word lists.
    """
    fillers = {
        'ar': ['آ', 'إ', 'أقصد', 'يعني', 'آآ', 'إإ'],
        'fr': ['euh', 'heu', "c'est-à-dire", 'voilà', 'donc'],
        'en': ['um', 'uh', 'er', 'like', 'you know', 'i mean']
    }
    filler_list = fillers.get(language, fillers['en'])
    found = []
    for seg in segments:
        for w in seg.get('words', []):
            if w['word'].strip().lower() in filler_list:
                found.append({
                    'word': w['word'].strip(),
                    'at_seconds': round(w['start'], 1)
                })
    return found


def detect_low_confidence_words(segments: list, threshold: float = 0.6) -> list:
    """
    Flag words Whisper was uncertain about (probability < threshold).
    These often correspond to mumbled words, false starts, or lapsus linguae.
    """
    low_conf = []
    for seg in segments:
        for w in seg.get('words', []):
            if w.get('probability', 1.0) < threshold:
                low_conf.append({
                    'word': w['word'].strip(),
                    'at_seconds': round(w['start'], 1),
                    'confidence': w['probability']
                })
    return low_conf


def detect_number_errors(source_script: str, transcript_text: str) -> list:
    """
    Extract all numbers from the source speech and check if they appear
    in the student's transcript. Missing numbers = likely error.
    Requirement D7 from cahier des charges.
    """
    # Match integers and decimals in both Western and Arabic-Indic numerals
    number_pattern = r'\b[\d٠-٩]+(?:[.,][\d٠-٩]+)?\b'
    source_numbers = re.findall(number_pattern, source_script)
    transcript_numbers = re.findall(number_pattern, transcript_text)
    missing = [n for n in source_numbers if n not in transcript_numbers]
    return missing


def run_full_analysis(source_script: str, transcript: dict, language: str = 'ar') -> dict:
    """
    Run all error detection functions and return a structured report.
    This is the main function called by the /evaluate endpoint.
    """
    segments = transcript.get('segments', [])
    full_text = transcript.get('full_text', '')

    return {
        'long_silences':        detect_long_silences(segments),
        'repetitions':          detect_repetitions(segments),
        'hesitation_words':     detect_hesitation_words(segments, language),
        'low_confidence_words': detect_low_confidence_words(segments),
        'number_errors':        detect_number_errors(source_script, full_text),
        'summary': {
            'silence_count':     len(detect_long_silences(segments)),
            'repetition_count':  len(detect_repetitions(segments)),
            'hesitation_count':  len(detect_hesitation_words(segments, language)),
            'number_errors':     len(detect_number_errors(source_script, full_text)),
        }
    }


# ── Endpoints ────────────────────────────────────────────────────────────────

@module_d_bp.route('/evaluate', methods=['POST'])
def evaluate():
    """
    Analyze a student transcript against the source speech.

    Request body (JSON):
      source_script   str   the original speech text (from Module A)
      transcript      dict  the Whisper output (from Module C)
      language        str   target language of the student's interpretation

    Response (JSON):
      long_silences, repetitions, hesitation_words,
      low_confidence_words, number_errors, summary
    """
    data = request.get_json()
    if not data or 'transcript' not in data:
        return jsonify({'error': 'transcript is required'}), 400

    try:
        report = run_full_analysis(
            source_script=data.get('source_script', ''),
            transcript=data['transcript'],
            language=data.get('language', 'ar')
        )
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@module_d_bp.route('/feedback', methods=['POST'])
def generate_feedback():
    """
    Full evaluation: combines algorithmic detection + LLM multi-agent analysis.

    Request body (JSON):
      source_script   str   the original source speech (from Module A)
      transcript_text str   the student's transcribed interpretation
      transcript      dict  full Whisper output with segments (for algorithmic)
      language        str   'ar'|'fr'|'en'

    Response (JSON):
      overall_score, language_errors, auto_corrections, false_starts,
      lapsus_linguae, terminology_problems, information_loss,
      strengths, recommendations, summary, algorithmic
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    source_script  = data.get('source_script', '')
    transcript_text = data.get('transcript_text', '')
    transcript_obj  = data.get('transcript', {})
    language        = data.get('language', 'ar')

    if not transcript_text:
        return jsonify({'error': 'transcript_text is required'}), 400

    # Run algorithmic analysis on segments
    algo = run_full_analysis(source_script, transcript_obj, language) if transcript_obj else {
        'long_silences': [], 'repetitions': [], 'hesitation_words': [],
        'number_errors': [], 'summary': {}
    }
    s = algo.get('summary', {})

    if not GROQ_API_KEY:
        return jsonify({'error': 'GROQ_API_KEY not configured', 'algorithmic': algo}), 500

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        prompt = LLM_ANALYSIS_PROMPT.format(
            language={'ar': 'Arabic', 'fr': 'French', 'en': 'English'}.get(language, language),
            source=source_script or '(source speech not provided)',
            transcript=transcript_text,
            silence_count=s.get('silence_count', 0),
            repetition_count=s.get('repetition_count', 0),
            hesitation_count=s.get('hesitation_count', 0),
            number_errors=s.get('number_errors', 0)
        )

        response = client.chat.completions.create(
            model=PRIMARY_LLM_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are an expert interpreter training evaluator at ETIB Beirut. '
                        'You return only valid JSON for pedagogical evaluation reports.'
                    )
                },
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=2000,
            temperature=0.2
        )

        llm_result = _extract_json(response.choices[0].message.content)
        llm_result['algorithmic'] = {
            'long_silences':    algo.get('long_silences', []),
            'repetitions':      algo.get('repetitions', []),
            'hesitation_words': algo.get('hesitation_words', []),
            'number_errors':    algo.get('number_errors', []),
            'summary':          s
        }
        return jsonify(llm_result)

    except json.JSONDecodeError as e:
        return jsonify({'error': f'JSON parse error: {e}', 'algorithmic': algo}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@module_d_bp.route('/history/<session_id>')
def get_history(session_id: str):
    """
    Retrieve performance history for adaptive difficulty.
    Requirement D11-D12 from cahier des charges.
    TODO: Person 5 — implement in Week 5.
    """
    return jsonify({'status': 'not yet implemented — planned for Week 5'}), 501
