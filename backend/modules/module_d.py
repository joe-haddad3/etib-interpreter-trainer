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
import os
import re
import json
import uuid
from flask import Blueprint, request, jsonify
from config import GROQ_API_KEY, PRIMARY_LLM_MODEL, UPLOAD_FOLDER


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

THIS IS AN INTERPRETATION TASK — NOT A READING TASK.
The student heard a speech in {source_language} and interpreted it into {target_language}.
The two texts are in DIFFERENT languages. Do NOT compare them word-for-word.
Compare MEANING, CONCEPTS, NUMBERS, and TERMINOLOGY across languages.

SOURCE SPEECH (in {source_language}):
{source}

STUDENT INTERPRETATION TRANSCRIPT (in {target_language}, raw ASR output):
{transcript}

AUTOMATICALLY DETECTED ISSUES (algorithmic):
- Long silences (> 1.5s gaps): {silence_count} detected
- Word repetitions: {repetition_count} detected → examples: {repetition_examples}
- Hesitation markers: {hesitation_count} detected → examples: {hesitation_examples}
- Number reproduction errors: {number_errors} detected

LOW-CONFIDENCE WORDS (Whisper was uncertain about these — possible pronunciation issues):
{uncertain_words}

EVALUATION TASKS — check every category thoroughly:

TASK 1 — TRANSLATION ACCURACY:
Go through each key concept, argument, and sentence of the source speech.
Did the student convey the correct meaning in {target_language}?
Flag any concept that was mistranslated, distorted, or given the wrong equivalent.
Example: source says "sustainable development", student said "développement durable" (correct) vs "développement stable" (wrong).

TASK 2 — CONTENT COVERAGE:
List every important idea, fact, number, name, or argument from the source speech.
For each one, state whether it was COVERED, PARTIALLY COVERED, or MISSING in the student's interpretation.
Give a coverage_score from 0 to 10.

TASK 3 — PRONUNCIATION FLAGS:
The uncertain words listed above are words Whisper was not confident about.
This often means the student pronounced them unclearly or incorrectly.
For each uncertain word, note: what word was likely intended, and what the likely pronunciation issue is.
In {target_language}: check gender agreement, liaison errors (French), or case endings (Arabic).

TASK 4 — FLUENCY ISSUES IN {target_language}:
- Hesitations: آ، يعني، أقصد (Arabic) / euh, heu, ben (French) / um, uh, er (English)
- Repetitions: words said twice in a row
- False starts: phrases that stop abruptly
- Auto-corrections: student corrects themselves mid-sentence
- Lapsus linguae: wrong word slipped out

TASK 5 — LANGUAGE QUALITY IN {target_language}:
Grammar errors in the INTERPRETATION language (not the source):
- Arabic: wrong case endings (إعراب), verb agreement, wrong تشكيل
- French: gender agreement, wrong tense, wrong preposition
- English: tense, subject-verb agreement

TASK 6 — NUMBERS AND DATES:
Extract every number, percentage, date, statistic from the SOURCE speech.
Check each one in the STUDENT interpretation. Flag wrong or missing numbers.

TASK 7 — TERMINOLOGY:
Key domain-specific terms from the source — were they rendered with the correct equivalent in the target language?

Give overall_score 0-10 and coverage_score 0-10:
- 9-10: Excellent — near-complete, accurate, fluent
- 7-8: Good — minor gaps or errors
- 5-6: Acceptable — several issues but core meaning preserved
- 3-4: Weak — significant mistranslations or information loss
- 0-2: Very poor — incomplete or incomprehensible

Return ONLY valid compact JSON (no markdown, no explanation outside the JSON):
{{
  "overall_score": 7.5,
  "coverage_score": 8.0,
  "translation_errors": [
    {{"source_text": "exact phrase from source in {source_language}", "student_said": "what student said in {target_language}", "correct_translation": "correct equivalent", "explanation": "why this is wrong"}}
  ],
  "missing_content": [
    {{"content": "idea or fact that was completely omitted", "importance": "high"}}
  ],
  "pronunciation_flags": [
    {{"word": "uncertain word", "confidence": 0.4, "likely_issue": "what was probably wrong about the pronunciation"}}
  ],
  "language_errors": [{{"text": "exact quote from student", "explanation": "grammar issue", "correction": "correct form"}}],
  "auto_corrections": [{{"text": "the corrected phrase"}}],
  "false_starts": [{{"text": "incomplete phrase"}}],
  "lapsus_linguae": [{{"text": "slip", "likely_intended": "intended word"}}],
  "terminology_problems": [{{"source_term": "term in source language", "student_used": "what student said", "correct_equivalent": "correct target language term"}}],
  "information_loss": [{{"lost_content": "what was omitted", "importance": "high"}}],
  "strengths": ["specific strength observed"],
  "recommendations": ["specific actionable recommendation"],
  "summary": "2-3 sentence overall assessment of interpretation quality."
}}
"""

module_d_bp = Blueprint('module_d', __name__)


# ── Error detection (algorithmic — no LLM calls, always free) ────────────────

# ── Hesitation word lists (all languages — Lebanese Arabic uses French fillers too) ──
HESITATION_PATTERNS = {
    'ar': [
        r'\bآ+\b', r'\bإ+\b', r'\bأممم+\b', r'\bممم+\b', r'\bيعني\b', r'\bأقصد\b',
        r'\beuh+\b', r'\bheu+\b', r'\bum+\b', r'\buh+\b', r'\bhmm+\b', r'\bhm+\b',
        r'\bben\b', r'\bvoilà\b', r'\bdonc\b',
    ],
    'fr': [r'\beuh+\b', r'\bheu+\b', r'\bhm+\b', r'\bvoilà\b', r'\bdonc\b', r'\bben\b', r'\bquoi\b'],
    'en': [r'\bum+\b', r'\buh+\b', r'\ber+\b', r'\bhmm+\b', r'\bhm+\b', r'\blike\b'],
}


def detect_hesitations_from_text(full_text: str, language: str = 'ar') -> list:
    """Detect hesitation markers in transcript text using regex — works without word timestamps."""
    patterns = HESITATION_PATTERNS.get(language, HESITATION_PATTERNS['en'])
    # Lebanese Arabic: also check French + English fillers
    if language == 'ar':
        patterns = HESITATION_PATTERNS['ar']
    found = []
    for pat in patterns:
        for m in re.finditer(pat, full_text, re.IGNORECASE):
            found.append({'word': m.group(), 'at_char': m.start()})
    # Remove duplicates
    seen = set()
    unique = []
    for f in found:
        key = (f['word'].lower(), f['at_char'])
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique


def detect_repetitions_from_text(full_text: str) -> list:
    """Detect consecutive word repetitions from transcript text — works without word timestamps."""
    # Strip punctuation for comparison
    words = re.findall(r'[\w؀-ۿ]+', full_text.lower())
    repetitions = []
    for i in range(len(words) - 1):
        if words[i] == words[i + 1] and len(words[i]) > 1:
            repetitions.append({'word': words[i], 'position': i})
    return repetitions


def detect_long_silences(segments: list, threshold_seconds: float = 1.5) -> list:
    """
    Detect gaps between segments longer than threshold.
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
    Run all error detection — combines word-level (when available) and text-based detection.
    Text-based detection works even when Groq transcript has no word timestamps.
    """
    segments  = transcript.get('segments', [])
    full_text = transcript.get('full_text', '')

    # Word-level detection (works when faster-whisper is used)
    silences        = detect_long_silences(segments)
    word_reps       = detect_repetitions(segments)
    word_hesitations = detect_hesitation_words(segments, language)
    low_conf        = detect_low_confidence_words(segments)
    number_errs     = detect_number_errors(source_script, full_text)

    # Text-based detection (always works, even with Groq transcript)
    text_hesitations = detect_hesitations_from_text(full_text, language)
    text_repetitions = detect_repetitions_from_text(full_text)

    # Merge: prefer word-level if available, otherwise use text-based
    all_hesitations = word_hesitations if word_hesitations else text_hesitations
    all_repetitions = word_reps if word_reps else text_repetitions

    return {
        'long_silences':        silences,
        'repetitions':          all_repetitions,
        'hesitation_words':     all_hesitations,
        'low_confidence_words': low_conf,
        'number_errors':        number_errs,
        'text_hesitations':     text_hesitations,
        'text_repetitions':     text_repetitions,
        'summary': {
            'silence_count':     len(silences),
            'repetition_count':  len(all_repetitions),
            'hesitation_count':  len(all_hesitations),
            'number_errors':     len(number_errs),
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

        rep_examples  = ', '.join(f'"{r["word"]}"' for r in (algo.get('repetitions', [])[:3]))
        hes_examples  = ', '.join(f'"{h["word"]}"' for h in (algo.get('hesitation_words', [])[:3]))

        prompt = LLM_ANALYSIS_PROMPT.format(
            language={'ar': 'Arabic', 'fr': 'French', 'en': 'English'}.get(language, language),
            source=source_script or '(source speech not provided)',
            transcript=transcript_text,
            silence_count=s.get('silence_count', 0),
            repetition_count=s.get('repetition_count', 0),
            repetition_examples=rep_examples or 'none found automatically',
            hesitation_count=s.get('hesitation_count', 0),
            hesitation_examples=hes_examples or 'none found automatically',
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


@module_d_bp.route('/full-evaluation', methods=['POST'])
def full_evaluation():
    """
    Complete evaluation from audio file.
    Re-transcribes with local faster-whisper to get word timestamps,
    then runs full algorithmic + LLM analysis.

    This endpoint fixes the core problem: Groq transcripts have no word
    timestamps, so hesitation/repetition algorithmic detection always returns 0.
    Local faster-whisper gives word-level data so all detectors work correctly.

    Request: multipart/form-data
      audio         file   student's recording
      source_script str    original speech text
      language      str    'ar'|'fr'|'en'

    Response: same as /feedback but with accurate algorithmic data + word scores
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'Audio file required'}), 400

    audio_file       = request.files['audio']
    source_script    = request.form.get('source_script', '')
    language         = request.form.get('language', 'ar')
    source_language  = request.form.get('source_language', language)

    ext       = os.path.splitext(audio_file.filename)[1] or '.webm'
    temp_path = os.path.join(UPLOAD_FOLDER, f'eval_{uuid.uuid4().hex[:8]}{ext}')
    audio_file.save(temp_path)

    try:
        # Use local faster-whisper: gives real segment timestamps (silence detection)
        # and word-level probabilities. Groq normalizes silence/repetitions away.
        from modules.module_c import _get_local_model
        model = _get_local_model()

        segments_iter, info = model.transcribe(
            temp_path,
            language=language,
            task='transcribe',
            word_timestamps=True,
            vad_filter=True,
            vad_parameters={'min_silence_duration_ms': 500},
            condition_on_previous_text=False,
        )

        full_text = ''
        all_segments = []
        all_word_scores = []

        for seg in segments_iter:
            seg_data = {
                'start': round(seg.start, 2),
                'end':   round(seg.end, 2),
                'text':  seg.text.strip(),
                'words': []
            }
            for w in (seg.words or []):
                seg_data['words'].append({
                    'word': w.word, 'start': round(w.start, 2),
                    'end': round(w.end, 2), 'probability': round(w.probability, 3)
                })
                all_word_scores.append({
                    'word':  w.word.strip(),
                    'start': round(w.start, 2),
                    'end':   round(w.end, 2),
                    'score': round(w.probability, 3),
                    'grade': 'good' if w.probability >= 0.8 else ('warn' if w.probability >= 0.65 else 'poor')
                })
            all_segments.append(seg_data)
            full_text += seg.text + ' '

        full_text = full_text.strip()
        transcript = {
            'full_text':           full_text,
            'segments':            all_segments,
            'language_detected':   info.language,
            'language_confidence': round(info.language_probability, 3),
            'duration_seconds':    round(info.duration, 1),
        }

        # Step 2: Full algorithmic analysis (now WITH word timestamps)
        algo = run_full_analysis(source_script, transcript, language)
        s    = algo.get('summary', {})

        # Step 3: LLM analysis with accurate data
        if not GROQ_API_KEY:
            return jsonify({'error': 'GROQ_API_KEY not configured', 'algorithmic': algo}), 500

        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        lang_names = {'ar': 'Arabic', 'fr': 'French', 'en': 'English'}
        rep_examples     = ', '.join(f'"{r.get("word","")}"' for r in algo.get('repetitions', [])[:3])
        hes_examples     = ', '.join(f'"{h.get("word","")}"' for h in algo.get('hesitation_words', [])[:3])
        uncertain_words  = [w for w in all_word_scores if w['grade'] == 'poor']
        uncertain_str    = ', '.join(
            f'"{w["word"]}" (confidence {w["score"]})'
            for w in uncertain_words[:10]
        ) or 'none flagged'

        prompt = LLM_ANALYSIS_PROMPT.format(
            source_language=lang_names.get(source_language, source_language),
            target_language=lang_names.get(language, language),
            source=source_script or '(source speech not provided)',
            transcript=full_text,
            silence_count=s.get('silence_count', 0),
            repetition_count=s.get('repetition_count', 0),
            repetition_examples=rep_examples or 'none found automatically',
            hesitation_count=s.get('hesitation_count', 0),
            hesitation_examples=hes_examples or 'none found automatically',
            number_errors=s.get('number_errors', 0),
            uncertain_words=uncertain_str,
        )

        response = client.chat.completions.create(
            model=PRIMARY_LLM_MODEL,
            messages=[
                {'role': 'system', 'content':
                 'You are an expert interpreter training evaluator at ETIB Beirut. '
                 'Return only valid JSON. Be thorough — detect ALL error types listed.'},
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

        # Step 4: Pronunciation scores from word data
        overall_pronun = (
            sum(w['score'] for w in all_word_scores) / len(all_word_scores)
            if all_word_scores else 0
        )
        uncertain_words = [w for w in all_word_scores if w['grade'] == 'poor']

        llm_result['pronunciation'] = {
            'words':         all_word_scores,
            'uncertain':     uncertain_words,
            'overall_score': round(overall_pronun, 3),
            'errors_found':  len(uncertain_words)
        }
        llm_result['transcript'] = transcript

        return jsonify(llm_result)

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


TASHKEEL_COMPARE_PROMPT = """You are an Arabic linguistics expert for ETIB (École de Traducteurs et d'Interprètes de Beyrouth, USJ Beirut).

SOURCE SPEECH generated by LLM (this is what the student should have interpreted — may contain tashkeel):
{source}

STUDENT INTERPRETATION TRANSCRIPT (what the student actually said):
{transcript}

Perform a DETAILED comparison. You must check EVERY key term.

TASK 1 — INFORMATION COMPLETENESS:
Go through the source speech sentence by sentence.
List every important concept, name, number, or argument that is MISSING from the student's transcript.

TASK 2 — TASHKEEL / إعراب ANALYSIS (Arabic case endings):
For each key word that appears in BOTH the source and the student transcript:
- What is the grammatical role of this word in the source sentence?
- What case ending (إعراب) should it have? (nominative ُ / accusative َ / genitive ِ / etc.)
- Based on the student's transcript context, did they likely use the correct case ending?
- If the word has tanween (تنوين): did the student likely use the correct nunation?

IMPORTANT: Even if the transcript doesn't show tashkeel, you can INFER from sentence structure
whether the student likely used the correct grammatical ending.

Return ONLY valid JSON:
{{
  "coverage_score": 8.5,
  "missing_content": [
    {{"content": "what was omitted", "importance": "high"}}
  ],
  "tashkeel_errors": [
    {{
      "word": "word without tashkeel",
      "expected_form": "word with correct tashkeel",
      "expected_case": "nominative — subject of verb",
      "likely_student_error": "probably said فتحة instead of ضمة",
      "explanation": "pedagogical explanation"
    }}
  ],
  "tashkeel_correct": [
    {{
      "word": "word",
      "form": "with tashkeel",
      "note": "correctly used"
    }}
  ],
  "overall_score": 7.5,
  "summary": "2-3 sentence assessment of information accuracy and Arabic case ending usage."
}}
"""


@module_d_bp.route('/tashkeel-compare', methods=['POST'])
def tashkeel_compare():
    """
    LLM text comparison between source speech (vocalized) and student transcript.
    Detects: missing information, wrong case endings (إعراب), tashkeel errors.
    No audio processing needed — pure text analysis.

    Request body (JSON):
      source_text   str  LLM-generated source speech (may have tashkeel)
      transcript    str  student's transcribed interpretation
      language      str  'ar' only (tashkeel is Arabic-specific)
    """
    data = request.get_json()
    if not data or not data.get('transcript'):
        return jsonify({'error': 'transcript required'}), 400

    source_text = data.get('source_text', '')
    transcript  = data.get('transcript', '')
    language    = data.get('language', 'ar')

    if language != 'ar':
        return jsonify({'error': 'Tashkeel comparison is for Arabic only'}), 400

    if not GROQ_API_KEY:
        return jsonify({'error': 'GROQ_API_KEY not configured'}), 500

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model=PRIMARY_LLM_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'You are an Arabic linguistics expert for interpreter training. '
                        'You perform detailed text comparison and إعراب analysis. '
                        'Return only valid JSON.'
                    )
                },
                {
                    'role': 'user',
                    'content': TASHKEEL_COMPARE_PROMPT.format(
                        source=source_text or '(source speech not provided)',
                        transcript=transcript
                    )
                }
            ],
            max_tokens=2000,
            temperature=0.1
        )

        result = _extract_json(response.choices[0].message.content)
        return jsonify(result)

    except json.JSONDecodeError as e:
        return jsonify({'error': f'JSON parse error: {e}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@module_d_bp.route('/pronunciation', methods=['POST'])
def pronunciation_report():
    """
    Generate a full pronunciation report from alignment results.

    Request body (JSON):
      alignment     dict   output from /api/module-c/align
      source_text   str    vocalized source speech
      language      str    'ar'|'fr'|'en'

    Response (JSON):
      overall_score       float
      word_display        list [{word, score, grade, expected_form?, likely_error?}]
      errors_found        int
      summary             str
    """
    data     = request.get_json()
    if not data or 'alignment' not in data:
        return jsonify({'error': 'alignment result required'}), 400

    alignment    = data['alignment']
    source_text  = data.get('source_text', '')
    language     = data.get('language', 'ar')

    words        = alignment.get('words', [])
    llm_analysis = alignment.get('llm_analysis', [])
    overall      = alignment.get('overall_score', 0)

    # Merge LLM analysis into word list for display
    llm_map = {item.get('word', ''): item for item in llm_analysis}
    enriched = []
    for w in words:
        entry = {**w}
        analysis = llm_map.get(w['word'], {})
        if analysis:
            entry['expected_form']  = analysis.get('expected_form', '')
            entry['likely_error']   = analysis.get('likely_error', '')
            entry['grammatical_role'] = analysis.get('grammatical_role', '')
            entry['explanation']    = analysis.get('explanation', '')
        enriched.append(entry)

    errors_found = len([w for w in words if w.get('grade') == 'poor'])

    # Build summary
    if overall >= 0.85:
        summary = 'Excellent pronunciation. Very few uncertain words detected.'
    elif overall >= 0.70:
        summary = f'Good pronunciation overall. {errors_found} word(s) may need attention.'
    elif overall >= 0.55:
        summary = f'Moderate pronunciation confidence. {errors_found} word(s) show significant uncertainty.'
    else:
        summary = f'Low pronunciation confidence detected. {errors_found} word(s) need practice.'

    return jsonify({
        'overall_score': overall,
        'word_display':  enriched,
        'errors_found':  errors_found,
        'summary':       summary,
        'whisperx_used': alignment.get('whisperx_used', False)
    })


@module_d_bp.route('/history/<session_id>')
def get_history(session_id: str):
    """
    Retrieve performance history for adaptive difficulty.
    Requirement D11-D12 from cahier des charges.
    TODO: Person 5 — implement in Week 5.
    """
    return jsonify({'status': 'not yet implemented — planned for Week 5'}), 501
