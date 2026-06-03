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
from flask import Blueprint, request, jsonify
from config import GROQ_API_KEY, PRIMARY_LLM_MODEL

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
    Generate a natural-language feedback report using the LLM.
    Takes the structured error report from /evaluate and writes human feedback.

    Request body (JSON):
      error_report    dict  output from /evaluate
      params_used     dict  the speech parameters (domain, language, difficulty)
      target_language str   language for the feedback text itself

    Response (JSON):
      feedback_text   str   the written feedback report

    TODO: Person 5 — implement in Week 4.
    """
    return jsonify({'status': 'not yet implemented — planned for Week 4'}), 501


@module_d_bp.route('/history/<session_id>')
def get_history(session_id: str):
    """
    Retrieve performance history for adaptive difficulty.
    Requirement D11-D12 from cahier des charges.
    TODO: Person 5 — implement in Week 5.
    """
    return jsonify({'status': 'not yet implemented — planned for Week 5'}), 501
