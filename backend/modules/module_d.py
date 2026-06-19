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
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, session as flask_session
from config import GROQ_API_KEY, PRIMARY_LLM_MODEL, UPLOAD_FOLDER

# ── Session storage (MongoDB when available, in-memory fallback) ──────────────
_mongo_sessions = None   # pymongo collection once connected
_mem_sessions: dict = {} # { user_id: [session, ...] }

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017')
MONGODB_DB  = os.getenv('MONGODB_DB', 'etib_interpreter_trainer')


def _get_sessions_collection():
    global _mongo_sessions
    if _mongo_sessions is not None:
        return _mongo_sessions
    try:
        from pymongo import MongoClient, ASCENDING, DESCENDING
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        col = client[MONGODB_DB]['evaluation_sessions']
        col.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)])
        _mongo_sessions = col
    except Exception:
        _mongo_sessions = None
    return _mongo_sessions


def _save_session(user_id: str, data: dict):
    """Persist one evaluation session; falls back to in-memory if no MongoDB."""
    doc = {
        'id':             str(uuid.uuid4()),
        'user_id':        user_id,
        'created_at':     datetime.now(timezone.utc).isoformat(),
        'language':       data.get('language', ''),
        'source_language': data.get('source_language', ''),
        'domain':         data.get('domain', ''),
        'overall_score':  data.get('overall_score', 0),
        'fluency_score':  data.get('fluency_score', 0),
        'coverage_score': data.get('coverage_score', 0),
        'error_counts': {
            'long_silences':    len(data.get('algorithmic', {}).get('long_silences', [])),
            'repetitions':      len(data.get('algorithmic', {}).get('repetitions', [])),
            'hesitation_words': len(data.get('algorithmic', {}).get('hesitation_words', [])),
            'number_errors':    len(data.get('algorithmic', {}).get('number_errors', [])),
            'information_loss': len(data.get('information_loss', [])),
            'translation_errors': len(data.get('translation_errors', [])),
        },
    }
    col = _get_sessions_collection()
    if col is not None:
        try:
            col.insert_one(doc)
            return
        except Exception:
            pass
    # In-memory fallback
    _mem_sessions.setdefault(user_id, []).append(doc)
    _mem_sessions[user_id] = _mem_sessions[user_id][-50:]   # keep last 50


def _load_sessions(user_id: str, limit: int = 20) -> list:
    col = _get_sessions_collection()
    if col is not None:
        try:
            docs = list(
                col.find({'user_id': user_id}, {'_id': 0})
                   .sort('created_at', -1)
                   .limit(limit)
            )
            return docs
        except Exception:
            pass
    sessions = _mem_sessions.get(user_id, [])
    return list(reversed(sessions))[:limit]


def _compute_adaptive_params(sessions: list) -> dict:
    """
    Analyse last sessions and return recommended Module A parameters (D11-D12).
    """
    if not sessions:
        return {'message': 'No sessions yet — complete at least one evaluation to get recommendations.'}

    recent = sessions[:10]
    avg_overall  = sum(s.get('overall_score', 0) for s in recent) / len(recent)
    avg_fluency  = sum(s.get('fluency_score', 0) for s in recent) / len(recent)
    avg_coverage = sum(s.get('coverage_score', 0) for s in recent) / len(recent)
    avg_numbers  = sum(s.get('error_counts', {}).get('number_errors', 0) for s in recent) / len(recent)
    avg_reps     = sum(s.get('error_counts', {}).get('repetitions', 0) for s in recent) / len(recent)
    avg_silences = sum(s.get('error_counts', {}).get('long_silences', 0) for s in recent) / len(recent)
    avg_info_loss = sum(s.get('error_counts', {}).get('information_loss', 0) for s in recent) / len(recent)

    # Start from reasonable defaults
    params = {
        'difficulty':     'intermediate',
        'word_count':     200,
        'number_density': 'medium',
        'speed_pressure': 'normal',
        'structure':      'well-organized',
        'topic_shifts':   'none',
    }
    tips = []

    # Overall performance → adjust difficulty / length
    if avg_overall >= 8.0:
        params['difficulty'] = 'advanced'
        params['word_count'] = 300
        tips.append('Excellent performance — raising difficulty to advanced.')
    elif avg_overall >= 6.5:
        params['difficulty'] = 'intermediate'
        params['word_count'] = 200
        tips.append('Good performance — maintaining intermediate difficulty.')
    else:
        params['difficulty'] = 'beginner'
        params['word_count'] = 120
        tips.append('Scores below 6.5 — stepping back to beginner level to build confidence.')

    # Number errors → push number density
    if avg_numbers >= 3:
        params['number_density'] = 'high'
        tips.append('Frequent number errors — training with high number density to drill accuracy.')
    elif avg_numbers <= 0.5 and avg_overall >= 7.0:
        params['number_density'] = 'medium'

    # Fluency (pauses/repetitions) → slow down
    if avg_fluency < 6.0 or avg_silences >= 2 or avg_reps >= 5:
        params['speed_pressure'] = 'slow'
        tips.append('Fluency needs work — slowing speech pace to reduce cognitive overload.')
    elif avg_fluency >= 8.0:
        params['speed_pressure'] = 'fast'
        tips.append('Strong fluency — increasing speaking pace.')

    # Content coverage / information loss → structure help
    if avg_info_loss >= 2 or avg_coverage < 6.0:
        params['structure'] = 'well-organized'
        tips.append('Missing content regularly — keeping well-organized speeches to aid note-taking.')
    elif avg_overall >= 7.5 and avg_info_loss <= 0:
        params['structure'] = 'meandering'
        params['topic_shifts'] = 'occasional'
        tips.append('Strong coverage — introducing slight topic shifts to challenge anticipation.')

    return {
        'recommended_params': params,
        'based_on_sessions':  len(recent),
        'averages': {
            'overall_score':  round(avg_overall, 2),
            'fluency_score':  round(avg_fluency, 2),
            'coverage_score': round(avg_coverage, 2),
            'number_errors':  round(avg_numbers, 2),
            'repetitions':    round(avg_reps, 2),
            'long_silences':  round(avg_silences, 2),
        },
        'tips': tips,
    }


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
- Long silences (> 1.0s gaps): {silence_count} detected → details: {silence_examples}
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
Do NOT flag number formatting as a language error (e.g. "8,8 milliards" is correct French —
French uses a comma as the decimal separator, English uses a period). Whether the NUMBER VALUE
itself is correct is judged separately in TASK 10, not here.

TASK 6 — NUMBERS AND DATES:
Extract every number, percentage, date, statistic from the SOURCE speech.
Check each one in the STUDENT interpretation. Flag wrong or missing numbers.

TASK 7 — TERMINOLOGY:
Key domain-specific terms from the source — were they rendered with the correct equivalent in the target language?

TASK 8 — PAUSES & FLOW:
{silence_count} pause(s) longer than 1 second were detected: {silence_examples}
For each pause, judge whether it disrupted the flow of the interpretation (lost the thread, made the listener wait)
or was a natural processing pause for a consecutive/simultaneous interpreter.
For disruptive pauses, note what information was likely delayed or lost because of it.

TASK 9 — REPETITIONS:
{repetition_count} repeated word(s)/phrase(s) were detected: {repetition_examples}
For each, judge whether it is a meaningless disfluency (stalling while thinking) or a productive
self-correction (catching and fixing a mistake). Comment on what this reveals about the student's
processing under pressure.

TASK 10 — NUMBERS, DATES & STATISTICS (cross-language check):
Extract EVERY number, percentage, date, and statistic from the SOURCE speech.
For each one, find what the student actually said in {target_language} (numbers may appear as digits
or spelled out words — both count). Mark each as correct or incorrect.
A wrong number, date, or statistic is a SERIOUS interpretation error — it can mislead an entire
negotiation — so flag it clearly even if the rest of the sentence was fine.

TASK 11 — PRONUNCIATION IN {target_language}:
LOW-CONFIDENCE WORDS the speech recognizer was unsure about (often a sign of unclear or incorrect
pronunciation): {uncertain_words}
Give specific, actionable pronunciation feedback for {target_language}:
- Arabic: تشكيل/إعراب (case endings), emphatic vs plain consonants (ص/س، ض/د، ط/ت، ظ/ذ، ق/ك),
  hamza ء placement, تاء مربوطة pronunciation, vowel length (مد/قصر)
- French: nasal vowels, liaison, silent final letters, gender-driven endings affecting sound
- English: word stress, "th" sounds (θ/ð), vowel reduction in unstressed syllables
For each low-confidence word above, explain the likely mispronunciation and give the correct way to say it.

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
  "fluency_score": 7.0,
  "pause_analysis": {{
    "comment": "professor's overall comment on pacing and pauses",
    "problem_pauses": [{{"at_seconds": 12.4, "duration_seconds": 2.1, "impact": "what was likely delayed or lost because of this pause"}}]
  }},
  "repetition_analysis": {{
    "comment": "professor's comment on repetitions found — stalling vs productive self-correction"
  }},
  "number_accuracy": [
    {{"source_value": "50%", "expected_in_target": "what the student should have said", "student_said": "what the student actually said", "correct": false, "note": "explanation of the error"}}
  ],
  "pronunciation_assessment": {{
    "comment": "general pronunciation commentary for this target language",
    "issues": [{{"word": "uncertain word", "issue": "likely mispronunciation", "correction": "how to pronounce it correctly"}}]
  }},
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


def _is_noise_segment(text: str) -> bool:
    """
    True if a Whisper segment is a non-speech annotation (e.g. '[Bruit de fond]',
    '[Music]', '(applaudissements)') rather than actual student speech.
    Whisper can get stuck hallucinating these tags repeatedly over noisy/silent
    audio, which would otherwise be misread as dozens of word repetitions.
    """
    t = text.strip()
    return not t or t[0] in '[('


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


def detect_long_silences(segments: list, threshold_seconds: float = 1.0) -> list:
    """
    Detect gaps longer than threshold — both between segments AND between
    consecutive words within the same segment.

    Whisper (without VAD) often merges a whole utterance plus a mid-sentence
    pause into a single segment, so a gap between word timestamps can hide
    a real pause that a segment-level-only check would miss.
    Also detects leading silence (student slow to start).
    """
    silences = []
    if not segments:
        return silences

    # Leading silence: if first segment starts after threshold
    if segments[0]['start'] >= threshold_seconds:
        silences.append({
            'at_seconds': 0.0,
            'duration_seconds': round(segments[0]['start'], 1),
            'after_text': '[start of recording]',
            'type': 'leading'
        })

    # Gaps between segments
    for i in range(len(segments) - 1):
        gap = round(segments[i + 1]['start'] - segments[i]['end'], 2)
        if gap >= threshold_seconds:
            silences.append({
                'at_seconds': round(segments[i]['end'], 1),
                'duration_seconds': gap,
                'after_text': segments[i].get('text', '')[-60:].strip(),
                'type': 'mid'
            })

    # Gaps between consecutive words within a segment (catches pauses that
    # don't get their own segment boundary)
    for seg in segments:
        words = seg.get('words', [])
        for i in range(len(words) - 1):
            gap = round(words[i + 1]['start'] - words[i]['end'], 2)
            if gap >= threshold_seconds:
                silences.append({
                    'at_seconds': round(words[i]['end'], 1),
                    'duration_seconds': gap,
                    'after_text': words[i].get('word', '').strip(),
                    'type': 'mid'
                })

    silences.sort(key=lambda s: s['at_seconds'])
    return silences


def detect_repetitions(segments: list) -> list:
    """
    Detect word repetitions:
    - Immediate repetitions (the the)
    - Near repetitions: same word within a 6-word window (I think... I think)
    - Short phrase repetitions (2-3 word sequences)
    """
    all_words = []
    for seg in segments:
        for w in seg.get('words', []):
            clean = re.sub(r'[^\w]', '', w['word'].strip().lower())
            if clean and len(clean) > 1:
                all_words.append({'word': clean, 'start': w.get('start', 0)})

    if not all_words:
        return []

    repetitions = []
    seen_positions = set()
    WINDOW = 8
    STOP_WORDS = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'of',
                  'is', 'was', 'are', 'were', 'i', 'it', 'that', 'this', 'with', 'for',
                  'les', 'le', 'la', 'des', 'de', 'du', 'et', 'en', 'un', 'une',
                  'je', 'il', 'elle', 'nous', 'que', 'qui', 'dans'}

    for i in range(len(all_words)):
        if i in seen_positions:
            continue
        word = all_words[i]['word']
        if word in STOP_WORDS or len(word) < 3:
            continue
        # Look ahead in window
        for j in range(i + 1, min(i + WINDOW, len(all_words))):
            if j in seen_positions:
                continue
            if all_words[j]['word'] == word:
                repetitions.append({
                    'word': word,
                    'at_seconds': round(all_words[i]['start'], 1),
                    'second_occurrence': round(all_words[j]['start'], 1),
                    'gap_words': j - i
                })
                seen_positions.add(i)
                seen_positions.add(j)
                break

    return repetitions


def detect_hesitation_words(segments: list, language: str = 'ar') -> list:
    """
    Detect filler / hesitation words with comprehensive per-language lists.
    """
    fillers = {
        'ar': {'آ', 'إ', 'أقصد', 'يعني', 'آآ', 'إإ', 'أممم', 'ممم', 'اممم'},
        'fr': {'euh', 'heu', 'hem', 'hm', 'ben', 'beh', 'voilà', 'donc', 'quoi',
               'enfin', 'genre', 'disons', 'comment', 'bref'},
        'en': {'um', 'uh', 'er', 'hmm', 'hm', 'like', 'basically', 'literally',
               'actually', 'right', 'okay', 'so', 'well', 'anyway', 'you know'}
    }
    # Lebanese Arabic students use French and English fillers too
    if language == 'ar':
        filler_set = fillers['ar'] | {'euh', 'heu', 'um', 'uh', 'hmm'}
    else:
        filler_set = fillers.get(language, fillers['en'])

    found = []
    for seg in segments:
        for w in seg.get('words', []):
            clean = w['word'].strip().lower().rstrip('.,!?')
            if clean in filler_set:
                found.append({
                    'word': w['word'].strip(),
                    'at_seconds': round(w.get('start', 0), 1),
                    'confidence': round(w.get('probability', 1.0), 3)
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


def build_pronunciation_report(all_word_scores: list, language: str) -> dict:
    """
    Build a pronunciation report using:
    1. Whisper word confidence (low confidence = likely mispronounced)
    2. Language-specific common error patterns

    Note: reference diffing against the source script is intentionally NOT done here —
    this is an interpretation task, so the source and the transcript are in different
    languages and a word-for-word diff between them is meaningless.
    """
    uncertain = [w for w in all_word_scores if w['grade'] == 'poor']
    warn_words = [w for w in all_word_scores if w['grade'] == 'warn']
    overall = (sum(w['score'] for w in all_word_scores) / len(all_word_scores)) if all_word_scores else 0

    # Language-specific patterns flagged from uncertain words
    flagged = []
    for w in uncertain:
        note = ''
        word = w['word'].lower()
        if language == 'fr':
            if word.endswith('ent') and len(word) > 5:
                note = 'Verb ending -ent is silent — check liaison'
            elif word in ('les', 'des', 'mes', 'ses', 'ces'):
                note = 'Liaison with next vowel required'
            elif any(word.endswith(s) for s in ('tion', 'sion')):
                note = 'French -tion/-sion pronounced /sjɔ̃/ — not like English'
        elif language == 'en':
            if len(word) > 7:
                note = 'Complex word — check stress pattern'
            elif word.endswith('ed'):
                note = '-ed suffix: /t/, /d/ or /ɪd/ depending on preceding sound'
            elif word.endswith('ough'):
                note = 'Irregular -ough spelling (through/though/thought all differ)'
        elif language == 'ar':
            raw = w['word'].strip()
            if any(ch in raw for ch in ('ً', 'ٌ', 'ٍ')):
                note = 'تنوين (tanween) detected — make sure the final vowel is pronounced clearly'
            elif 'ّ' in raw:
                note = 'شدّة (shadda) — the consonant must be doubled/geminated, not pronounced once'
            elif 'ة' in raw:
                note = 'تاء مربوطة — pronounced as /a/ in pause, but as /at/ when followed by another word (إعراب)'
            elif any(ch in raw for ch in ('ص', 'ض', 'ط', 'ظ')):
                note = 'Emphatic letter (ص/ض/ط/ظ) — needs a deeper, "heavier" articulation than its plain counterpart (س/د/ت/ذ)'
            elif 'ق' in raw:
                note = 'ق (qaf) — uvular sound, do not replace with ك (kaf) or hamza'
            elif 'ء' in raw or 'أ' in raw or 'إ' in raw:
                note = 'Hamza (ء) — must be articulated as a clear glottal stop, not dropped'
            elif any(ch in raw for ch in ('ث', 'ذ', 'ظ')):
                note = 'Interdental letter (ث/ذ/ظ) — tongue between teeth, do not replace with س/ز/ز'
            elif any(ch in raw for ch in ('ع', 'غ')):
                note = 'Pharyngeal/guttural letter (ع/غ) — produced deep in the throat, distinct from ا/خ'
        flagged.append({
            'word': w['word'],
            'start': w.get('start', 0),
            'confidence': w['score'],
            'grade': 'poor',
            'note': note or f'Low recognition confidence ({int(w["score"]*100)}%) — review pronunciation'
        })

    return {
        'overall_score': round(overall, 3),
        'total_words': len(all_word_scores),
        'uncertain_count': len(uncertain),
        'warn_count': len(warn_words),
        'flagged_words': flagged,
        'summary': (
            f'Good pronunciation confidence ({int(overall*100)}%).'
            if overall >= 0.8
            else f'{len(uncertain)} word(s) flagged with low confidence ({int(overall*100)}% average). Review highlighted words.'
        )
    }


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
        sil_examples  = '; '.join(
            f'{sl["duration_seconds"]}s' + (f' after "{sl["after_text"]}"' if sl.get('after_text') else '')
            for sl in algo.get('long_silences', [])[:5]
        )

        lang_names = {'ar': 'Arabic', 'fr': 'French', 'en': 'English'}
        prompt = LLM_ANALYSIS_PROMPT.format(
            source_language=lang_names.get(data.get('source_language', language), language),
            target_language=lang_names.get(language, language),
            source=source_script or '(source speech not provided)',
            transcript=transcript_text,
            silence_count=s.get('silence_count', 0),
            silence_examples=sil_examples or 'none found automatically',
            repetition_count=s.get('repetition_count', 0),
            repetition_examples=rep_examples or 'none found automatically',
            hesitation_count=s.get('hesitation_count', 0),
            hesitation_examples=hes_examples or 'none found automatically',
            number_errors=s.get('number_errors', 0),
            uncertain_words='(not available in text-only mode)',
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
        from modules.module_c import _get_local_model, DISFLUENCY_PROMPTS
        model = _get_local_model()

        segments_iter, info = model.transcribe(
            temp_path,
            language=language,
            task='transcribe',
            word_timestamps=True,
            vad_filter=False,               # disabled: preserves silence gaps between segments
            suppress_tokens=[],             # preserve fillers/repetitions, no normalization
            condition_on_previous_text=False,
            compression_ratio_threshold=100.0,  # disable repetition fallback — keeps repeated words
            log_prob_threshold=-100.0,          # disable low-prob fallback — keeps hesitations
            temperature=0.0,                    # greedy decoding — no randomness
            beam_size=1,                        # greedy: prevents beam search from collapsing repetitions
            initial_prompt=DISFLUENCY_PROMPTS.get(language, DISFLUENCY_PROMPTS['en']),  # primes Whisper to keep "euh/um" fillers
        )

        full_text = ''
        all_segments = []
        all_word_scores = []

        for seg in segments_iter:
            if _is_noise_segment(seg.text):
                continue
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
        sil_examples     = '; '.join(
            f'{sl["duration_seconds"]}s' + (f' after "{sl["after_text"]}"' if sl.get('after_text') else '')
            for sl in algo.get('long_silences', [])[:5]
        )
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
            silence_examples=sil_examples or 'none found automatically',
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

        # Step 4: Pronunciation report (whisper confidence + language-specific patterns)
        pronun_report = build_pronunciation_report(all_word_scores, language=language)
        llm_result['pronunciation'] = pronun_report
        llm_result['transcript'] = transcript

        # Step 5: Persist session for history / adaptive difficulty (D11-D12)
        user_id = flask_session.get('user_id', 'anonymous')
        _save_session(user_id, {
            **llm_result,
            'language':        language,
            'source_language': source_language,
            'domain':          request.form.get('domain', ''),
        })

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


@module_d_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """Return the last 20 evaluation sessions for the logged-in user (D11)."""
    user_id = flask_session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    limit = min(int(request.args.get('limit', 20)), 50)
    sessions = _load_sessions(user_id, limit=limit)
    return jsonify({'sessions': sessions, 'count': len(sessions)})


@module_d_bp.route('/adaptive-params', methods=['GET'])
def adaptive_params():
    """
    Analyse recent sessions and return recommended Module A parameters (D12).
    """
    user_id = flask_session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    sessions = _load_sessions(user_id, limit=10)
    return jsonify(_compute_adaptive_params(sessions))


@module_d_bp.route('/history/<session_id>')
def get_history(session_id: str):
    """Return a single session by id (D11)."""
    user_id = flask_session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    col = _get_sessions_collection()
    if col is not None:
        try:
            doc = col.find_one({'id': session_id, 'user_id': user_id}, {'_id': 0})
            if doc:
                return jsonify(doc)
        except Exception:
            pass
    for s in _mem_sessions.get(user_id, []):
        if s.get('id') == session_id:
            return jsonify(s)
    return jsonify({'error': 'Session not found'}), 404
