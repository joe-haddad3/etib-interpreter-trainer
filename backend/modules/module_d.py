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
from flask import Blueprint, request, jsonify
from config import PRIMARY_LLM_MODEL, UPLOAD_FOLDER

def _current_user_id() -> str:
    """Extract user id from auth token in request args, form, or JSON body."""
    try:
        from modules.auth import get_user_from_token
        token = (
            request.args.get('auth_token', '') or
            request.form.get('auth_token', '') or
            (request.get_json(silent=True) or {}).get('auth_token', '')
        ).strip()
        user = get_user_from_token(token)
        return user['id'] if user else 'anonymous'
    except Exception:
        return 'anonymous'

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


def _extract_top_errors(data: dict) -> list:
    """Pull the most important specific errors from an evaluation result for storage."""
    errors = []
    for te in (data.get('translation_errors') or [])[:3]:
        if isinstance(te, dict):
            errors.append({
                'type': 'translation',
                'source': str(te.get('source_text', ''))[:120],
                'said':   str(te.get('student_said', ''))[:120],
            })
    for na in (data.get('number_accuracy') or []):
        if isinstance(na, dict) and not na.get('correct'):
            errors.append({
                'type':     'number',
                'expected': str(na.get('expected_in_target', ''))[:80],
                'said':     str(na.get('student_said', ''))[:80],
            })
    for mc in (data.get('missing_content') or [])[:3]:
        if isinstance(mc, dict) and mc.get('importance') == 'high':
            errors.append({
                'type':   'missing',
                'detail': str(mc.get('content', ''))[:150],
            })
    return errors[:6]


def _save_session(user_id: str, data: dict):
    """Persist one evaluation session; falls back to in-memory if no MongoDB."""
    algo = data.get('algorithmic', {}) or {}
    doc = {
        'id':              str(uuid.uuid4()),
        'user_id':         user_id,
        'created_at':      datetime.now(timezone.utc).isoformat(),
        'language':        data.get('language', ''),
        'source_language': data.get('source_language', ''),
        'domain':          data.get('domain', ''),
        'overall_score':   data.get('overall_score') or 0,
        'fluency_score':   data.get('fluency_score') or 0,
        'coverage_score':  data.get('coverage_score') or 0,
        'error_counts': {
            'long_silences':     len(algo.get('long_silences') or []),
            'repetitions':       len(algo.get('repetitions') or []),
            'hesitation_words':  len(algo.get('hesitation_words') or []),
            'number_errors':     len(algo.get('number_errors') or []),
            'information_loss':  len(data.get('information_loss') or []),
            'translation_errors':len(data.get('translation_errors') or []),
            'missing_content':   len(data.get('missing_content') or []),
        },
        'top_errors':      _extract_top_errors(data),
        'recommendations': (data.get('recommendations') or [])[:5],
        'strengths':       (data.get('strengths') or [])[:3],
        'summary':         str(data.get('summary') or '')[:500],
    }
    col = _get_sessions_collection()
    if col is not None:
        try:
            col.insert_one(doc)
            return
        except Exception:
            pass
    _mem_sessions.setdefault(user_id, []).append(doc)
    _mem_sessions[user_id] = _mem_sessions[user_id][-50:]


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
    """Analyse sessions → recommended Module A params + problems to work on + trend."""
    if not sessions:
        return {
            'message': 'No sessions yet — complete at least one full evaluation to start tracking.',
            'problems_to_work_on': [],
            'trend': 'not_enough_data',
        }

    recent   = sessions[:10]
    older    = sessions[10:20]

    def avg(key, sub=None):
        vals = []
        for s in recent:
            v = s.get('error_counts', {}).get(key, 0) if sub == 'error' else s.get(key, 0)
            vals.append(v or 0)
        return sum(vals) / len(vals) if vals else 0

    avg_overall  = avg('overall_score')
    avg_fluency  = avg('fluency_score')
    avg_coverage = avg('coverage_score')
    avg_numbers  = avg('number_errors', 'error')
    avg_reps     = avg('repetitions', 'error')
    avg_silences = avg('long_silences', 'error')
    avg_info_loss = avg('information_loss', 'error')
    avg_trans    = avg('translation_errors', 'error')
    avg_missing  = avg('missing_content', 'error')

    # ── Trend detection ──────────────────────────────────────────────────────
    trend = 'not_enough_data'
    improvement_pct = None
    if len(sessions) >= 4:
        last3  = sessions[:3]
        prev   = sessions[3:min(8, len(sessions))]
        r_avg  = sum(s.get('overall_score', 0) for s in last3) / len(last3)
        p_avg  = sum(s.get('overall_score', 0) for s in prev)  / len(prev)
        delta  = r_avg - p_avg
        improvement_pct = round(delta, 2)
        if delta >= 0.8:
            trend = 'improving'
        elif delta <= -0.8:
            trend = 'declining'
        else:
            trend = 'stable'

    # ── Problems to work on ──────────────────────────────────────────────────
    problems = []

    def severity(ratio):
        if ratio >= 0.7: return 'high'
        if ratio >= 0.4: return 'medium'
        return 'low'

    n = len(recent)
    sessions_with_trans    = sum(1 for s in recent if s.get('error_counts', {}).get('translation_errors', 0) > 0)
    sessions_with_numbers  = sum(1 for s in recent if s.get('error_counts', {}).get('number_errors', 0) > 0)
    sessions_with_silences = sum(1 for s in recent if s.get('error_counts', {}).get('long_silences', 0) >= 2)
    sessions_with_reps     = sum(1 for s in recent if s.get('error_counts', {}).get('repetitions', 0) >= 3)
    sessions_with_missing  = sum(1 for s in recent if s.get('error_counts', {}).get('missing_content', 0) >= 2)
    sessions_with_coverage = sum(1 for s in recent if (s.get('coverage_score') or 10) < 7)
    sessions_with_fluency  = sum(1 for s in recent if (s.get('fluency_score') or 10) < 6.5)

    if sessions_with_trans / n >= 0.3:
        problems.append({'key': 'translation', 'label': 'Translation accuracy', 'severity': severity(sessions_with_trans / n), 'detail': f'Wrong equivalents in {sessions_with_trans}/{n} sessions', 'tip': 'Study terminology lists and practice active listening for key concepts.'})
    if sessions_with_numbers / n >= 0.3:
        problems.append({'key': 'numbers', 'label': 'Numbers & figures', 'severity': severity(sessions_with_numbers / n), 'detail': f'Number errors in {sessions_with_numbers}/{n} sessions', 'tip': 'Practice shadowing speeches with high number density.'})
    if sessions_with_missing / n >= 0.3:
        problems.append({'key': 'missing', 'label': 'Missing content', 'severity': severity(sessions_with_missing / n), 'detail': f'Key ideas omitted in {sessions_with_missing}/{n} sessions', 'tip': 'Improve note-taking and work on shorter speeches first.'})
    if sessions_with_silences / n >= 0.3:
        problems.append({'key': 'silences', 'label': 'Long pauses', 'severity': severity(sessions_with_silences / n), 'detail': f'Excessive pauses in {sessions_with_silences}/{n} sessions', 'tip': 'Practice décalage (time-lag) exercises to keep output flowing.'})
    if sessions_with_reps / n >= 0.3:
        problems.append({'key': 'repetitions', 'label': 'Repetitions & self-corrections', 'severity': severity(sessions_with_reps / n), 'detail': f'High repetitions in {sessions_with_reps}/{n} sessions', 'tip': 'Work on reformulation — commit to a rendering instead of backtracking.'})
    if sessions_with_fluency / n >= 0.4:
        problems.append({'key': 'fluency', 'label': 'Delivery fluency', 'severity': severity(sessions_with_fluency / n), 'detail': f'Low fluency score in {sessions_with_fluency}/{n} sessions', 'tip': 'Shadow native speakers and record yourself daily.'})
    if sessions_with_coverage / n >= 0.4:
        problems.append({'key': 'coverage', 'label': 'Content coverage', 'severity': severity(sessions_with_coverage / n), 'detail': f'Low coverage in {sessions_with_coverage}/{n} sessions', 'tip': 'Focus on conveying main ideas before worrying about style.'})

    # Sort: high severity first
    sev_order = {'high': 0, 'medium': 1, 'low': 2}
    problems.sort(key=lambda p: sev_order.get(p['severity'], 3))

    # ── Recommended params ───────────────────────────────────────────────────
    params = {'difficulty': 'intermediate', 'word_count': 200, 'number_density': 'medium',
              'speed_pressure': 'normal', 'structure': 'well-organized', 'topic_shifts': 'none'}
    tips = []

    if avg_overall >= 8.0:
        params['difficulty'] = 'advanced'; params['word_count'] = 300
        tips.append('Excellent performance — raising difficulty to advanced.')
    elif avg_overall >= 6.5:
        params['difficulty'] = 'intermediate'; params['word_count'] = 200
        tips.append('Good performance — maintaining intermediate difficulty.')
    else:
        params['difficulty'] = 'beginner'; params['word_count'] = 120
        tips.append('Scores below 6.5 — stepping back to beginner to build confidence.')

    if avg_numbers >= 3:
        params['number_density'] = 'high'
        tips.append('Frequent number errors — drilling with high number density.')
    elif avg_numbers <= 0.5 and avg_overall >= 7.0:
        params['number_density'] = 'medium'

    # Fluency (pauses/repetitions) → adjust pace (values must exist in the
    # Module A form: normal | fast | very_fast)
    if avg_fluency < 6.0 or avg_silences >= 2 or avg_reps >= 5:
        params['speed_pressure'] = 'normal'
        tips.append('Fluency needs work — keeping a normal pace; also try slowing the audio playback rate in Audio & Materials.')
    elif avg_fluency >= 8.0:
        params['speed_pressure'] = 'fast'
        tips.append('Strong fluency — increasing speaking pace.')

    # Content coverage / information loss → structure help (valid values:
    # well-organized | semi-structured | deliberately disorganized)
    if avg_info_loss >= 2 or avg_coverage < 6.0:
        params['structure'] = 'well-organized'
        tips.append('Missing content regularly — keeping well-organized speeches to aid note-taking.')
    elif avg_overall >= 7.5 and avg_info_loss <= 0:
        params['structure'] = 'semi-structured'
        params['topic_shifts'] = 'mild'
        tips.append('Strong coverage — introducing slight topic shifts to challenge anticipation.')

    return {
        'recommended_params':  params,
        'based_on_sessions':   len(recent),
        'trend':               trend,
        'improvement_pct':     improvement_pct,
        'problems_to_work_on': problems,
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


def _safe_format(template: str, **kwargs) -> str:
    """Format a prompt template without risking KeyError or prompt-injection when
    user-supplied speech text contains literal { or } characters.
    Strategy: double-escape braces in every value before calling str.format() so
    Python's format parser sees {{ / }} (literal braces) instead of format specs."""
    safe = {k: str(v).replace('{', '{{').replace('}', '}}') for k, v in kwargs.items()}
    return template.format(**safe)


# ── ASR artifact / garbage-token filtering ────────────────────────────────────
# Whisper sometimes hallucinates one character stretched dozens of times over
# unclear or noisy audio (e.g. "ڨيييييييييييييي"). These are not student speech
# and must never be shown as "what the student said" in a translation error.

_ELONGATED_RUN_RE = re.compile(r'(.)\1{4,}', flags=re.UNICODE)


_PURE_PUNCT_RE = re.compile(r'^[.…,;:!?\-–—]+$')

def is_asr_garbage_token(token: str) -> bool:
    """True if a token is an ASR hallucination artifact, not real speech."""
    t = str(token or '').strip()
    if not t:
        return False
    # Pure punctuation tokens like "..." that Groq inserts for silent audio
    if _PURE_PUNCT_RE.match(t):
        return True
    if len(t) < 6:
        return False
    if not _ELONGATED_RUN_RE.search(t):
        return False
    from collections import Counter
    most_common_count = Counter(t).most_common(1)[0][1]
    return (most_common_count / len(t)) >= 0.5


def remove_asr_artifacts(text: str) -> tuple[str, list[str]]:
    """Strip garbage tokens from a transcript. Returns (clean_text, artifacts)."""
    artifacts = []
    kept = []
    for token in str(text or '').split():
        if is_asr_garbage_token(token):
            artifacts.append(token[:40])
        else:
            kept.append(token)
    return ' '.join(kept), artifacts


def contains_asr_garbage(text: str) -> bool:
    return any(is_asr_garbage_token(token) for token in str(text or '').split())


def reclassify_garbage_translation_errors(result: dict) -> dict:
    """
    Move translation errors whose "student said" is an ASR artifact into
    missing_content as unclear audio — the audio was unintelligible there,
    which is a coverage/clarity problem, not a mistranslation.
    """
    if not isinstance(result, dict):
        return result

    kept = []
    missing = result.setdefault('missing_content', [])
    if not isinstance(missing, list):
        missing = []
        result['missing_content'] = missing

    for item in result.get('translation_errors', []) or []:
        if isinstance(item, dict) and contains_asr_garbage(item.get('student_said', '')):
            source_text = str(item.get('source_text', '')).strip()
            if source_text:
                missing.append({
                    'content': f'{source_text} — the recording was unclear at this point '
                               '(the recognizer could not identify real words)',
                    'importance': 'high',
                })
            continue
        kept.append(item)
    result['translation_errors'] = kept

    # Same cleanup for number accuracy: garbage "student said" means unclear
    # audio, and the number should be reported as missing, not substituted.
    for item in result.get('number_accuracy', []) or []:
        if isinstance(item, dict) and contains_asr_garbage(item.get('student_said', '')):
            item['student_said'] = '[unclear audio]'
            item['note'] = (str(item.get('note', '')).strip() + ' '
                            'The recording was unclear here — the number could not be recognized.').strip()
    return result


# ── Cross-language date/number equivalence (fixes false positives) ───────────
# "29 June 2026", "June 29, 2026" and "٢٩ يونيو ٢٠٢٦" are the SAME date.
# "8.8" and "8,8" are the same value (decimal separator differs by language).

_MONTH_NUMBERS = {
    # English
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8,
    'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    # French
    'janvier': 1, 'fevrier': 2, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5,
    'juin': 6, 'juillet': 7, 'aout': 8, 'août': 8, 'septembre': 9,
    'octobre': 10, 'novembre': 11, 'decembre': 12, 'décembre': 12,
    # Arabic (Levantine/MSA + transliterated Western months)
    'يناير': 1, 'فبراير': 2, 'مارس': 3, 'أبريل': 4, 'ابريل': 4, 'مايو': 5,
    'يونيو': 6, 'يوليو': 7, 'أغسطس': 8, 'اغسطس': 8, 'سبتمبر': 9,
    'أكتوبر': 10, 'اكتوبر': 10, 'نوفمبر': 11, 'ديسمبر': 12,
    'كانون الثاني': 1, 'شباط': 2, 'آذار': 3, 'اذار': 3, 'نيسان': 4, 'أيار': 5, 'ايار': 5,
    'حزيران': 6, 'تموز': 7, 'آب': 8, 'اب': 8, 'أيلول': 9, 'ايلول': 9,
    'تشرين الأول': 10, 'تشرين الاول': 10, 'تشرين الثاني': 11, 'كانون الأول': 12, 'كانون الاول': 12,
}

_ARABIC_INDIC_TO_WESTERN = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')


def extract_numeric_fingerprint(text: str) -> list[float]:
    """
    Extract every numeric value in a text (digits in any script, decimal comma
    or point, and month names) as a sorted list — a format-independent
    fingerprint. Two renderings of the same date/number produce equal lists.
    """
    normalized = str(text or '').translate(_ARABIC_INDIC_TO_WESTERN).lower()
    values: list[float] = []

    for phrase, month_number in _MONTH_NUMBERS.items():
        if phrase in normalized:
            values.append(float(month_number))
            normalized = normalized.replace(phrase, ' ')

    for match in re.finditer(r'\d+(?:[.,]\d+)?', normalized):
        raw = match.group(0)
        # A comma followed by exactly 3 digits is a thousands separator;
        # otherwise treat both , and . as decimal separators.
        if re.fullmatch(r'\d+,\d{3}', raw):
            raw = raw.replace(',', '')
        else:
            raw = raw.replace(',', '.')
        try:
            values.append(float(raw))
        except ValueError:
            continue

    return sorted(values)


def filter_equivalent_number_renderings(result: dict) -> dict:
    """
    Un-flag number_accuracy items where the student said the same values in a
    different valid format: date word-order across languages, Arabic-Indic vs
    Western digits, or decimal comma vs point.
    """
    items = result.get('number_accuracy') if isinstance(result, dict) else None
    if not isinstance(items, list):
        return result

    for item in items:
        if not isinstance(item, dict) or item.get('correct'):
            continue
        source_values = extract_numeric_fingerprint(
            item.get('source_value', '') or item.get('expected_in_target', '')
        )
        student_values = extract_numeric_fingerprint(item.get('student_said', ''))
        if source_values and source_values == student_values:
            item['correct'] = True
            item['note'] = (
                'Same value in a different valid format (date order, digit script, '
                'or decimal separator differ between languages) — not an error.'
            )
    return result


# ── Foreign-script cleanup in LLM output ──────────────────────────────────────
# The LLM occasionally emits stray CJK or other foreign-script characters
# inside Arabic corrections (e.g. "官ة شؤون السكان"). Those characters are
# never legitimate in this trilingual AR/FR/EN context.

_FOREIGN_SCRIPT_RE = re.compile(
    '[⺀-⿿　-〿぀-ヿ㄀-ㄯ㄰-㆏'
    '㐀-䶿一-鿿ꀀ-꓏가-힯豈-﫿'
    '\U00020000-\U0002EBEF]+'
)


def strip_foreign_script_chars(value):
    """Recursively remove CJK/foreign-script characters from all result strings."""
    if isinstance(value, str):
        return _FOREIGN_SCRIPT_RE.sub('', value)
    if isinstance(value, list):
        return [strip_foreign_script_chars(item) for item in value]
    if isinstance(value, dict):
        return {key: strip_foreign_script_chars(item) for key, item in value.items()}
    return value


LLM_ANALYSIS_PROMPT = """You are a professional interpreter training evaluator at ETIB (École de Traducteurs et d'Interprètes de Beyrouth, USJ Beirut).

THIS IS AN INTERPRETATION TASK — NOT A READING TASK.
The student heard a speech in {source_language} and interpreted it into {target_language}.
The two texts are in DIFFERENT languages. Compare MEANING, CONCEPTS, NUMBERS, and TERMINOLOGY.

YOU ARE A STRICT PROFESSOR. Your job is to FIND and REPORT errors, not to excuse them.
- If the student's rendering changes the meaning even slightly → flag it as a translation error.
- If a term is imprecise, vague, or weakened → flag it.
- If you find fewer than 3 translation errors in a student transcript that has obvious mistakes, you are being too lenient. Re-read and look harder.
- Do NOT give the student the benefit of the doubt. If something is wrong, say so clearly.

SOURCE SPEECH (in {source_language}):
{source}

STUDENT INTERPRETATION TRANSCRIPT (in {target_language}, raw ASR output):
{transcript}
{glossary_block}
AUTOMATICALLY DETECTED ISSUES (algorithmic):
- Long silences (> 2.0s gaps): {silence_count} detected → details: {silence_examples}
- Word repetitions: {repetition_count} detected → examples: {repetition_examples}
- Hesitation markers: {hesitation_count} detected → examples: {hesitation_examples}
  (A hesitation is ONLY a vocal filler — "euh", "um", "يعني", elongated sounds — or a word the
  student cut mid-way and restarted. Normal discourse words like "donc", "alors", "en fait",
  "like", "you know" are legitimate speech: NEVER count them as hesitations or disfluencies.)
- Number reproduction errors: {number_errors} detected
- Number error details: {number_error_details}
- Coverage length check: {coverage_diagnostics}

AUDIO-BASED FLUENCY AND RELIABILITY:
{fluency_summary}

LOW-CONFIDENCE WORDS (Whisper was uncertain about these — possible pronunciation issues):
{uncertain_words}

Important reliability rule:
- The transcript is an ASR estimate, not ground truth.
- Do not over-penalize meaning or terminology in low-confidence regions.
- Treat low-confidence words primarily as pronunciation/clarity evidence unless the surrounding meaning is clearly wrong.
- For French and English, use audio fluency metrics and word confidence as stronger evidence for delivery quality than the raw transcript wording.
- French-specific: do NOT mark a missing/omitted final plural "s" as an error from audio alone.
  French final plural endings are usually silent, so words like "délégué" and "délégués"
  are acoustically identical. Only flag singular/plural if surrounding audible grammar clearly proves
  the number is wrong, such as a wrong article, determiner, verb agreement, or changed meaning.

EVALUATION TASKS — check every category thoroughly:

TASK 1 — TRANSLATION ACCURACY (most important task — be thorough and strict):
Go through the source speech sentence by sentence. For each sentence ask:
"Did the student convey the EXACT meaning in {target_language}?"

Flag ALL of the following as translation_errors:
- Wrong word choice that changes meaning (e.g. "increase" when source said "decrease")
- A vague or weakened rendering (e.g. "problem" when source said "crisis")
- A term from the wrong domain (e.g. "durable" vs "développement durable")
- An opposite meaning (e.g. "approve" vs "reject")
- A concept rendered in a way a listener would understand differently

IMPORTANT: Do NOT put number, percentage, statistic, or date errors here — those are handled exclusively in TASK 10 (number_accuracy). translation_errors is only for meaning/wording errors.

CRITICAL EXCEPTION — official target-language abbreviations and equivalents:
When the student interprets into {target_language}, using the official {target_language}-language
name or abbreviation for an international body is ALWAYS correct — do NOT flag it as an error.
Examples (EN → FR): ESCWA → CESAO, SDGs → ODD, WHO → OMS, UNDP → PNUD, EU → UE.
Stating BOTH the source-language and target-language abbreviation together (e.g. "CESAO-ESCWA")
is also standard bilingual UN practice and must NOT be flagged as an error.

Do NOT accept these excuses:
- "close enough" — if meaning shifted, it is an error
- "approximate" — approximation is an error in interpretation
- "implied by context" — the student must say it, not imply it

List EVERY translation error you find. Do not stop early. Do not summarize multiple errors into one.
If the student said nothing for a source segment → put it under missing_content, not here.

TASK 2 — CONTENT COVERAGE:
List every important idea, fact, number, name, or argument from the source speech.
For each one, state whether it was COVERED, PARTIALLY COVERED, or MISSING in the student's interpretation.

CRITICAL RULES for coverage assessment:
- An idea is COVERED if the student expressed the same meaning in the target language, even with different words, structure, or phrasing. Paraphrase = covered.
- An idea is MISSING only if it is completely absent — not mentioned, not implied, not reformulated.
- Do NOT mark an idea as missing just because the student used fewer words than the source.
- Interpretation is always shorter than the source — a skilled interpreter conveys the same content in fewer, more direct words.
- The source and target languages are different — do not expect word-for-word translation.

coverage_score rubric (0–10, base this ONLY on content, not length or style):
- 9–10: All important ideas, facts, names, and numbers present
- 7–8: Almost all content covered; only minor or peripheral details missing
- 5–6: Main ideas present but several supporting facts or arguments missing
- 3–4: Some main ideas missing; significant information loss
- 0–2: Most content absent; interpretation is fragmentary

MANDATORY scoring rule: if missing_content is EMPTY (you found nothing genuinely missing),
coverage_score MUST be 9 or 10. If missing_content has only 1 minor item, coverage_score
MUST be at least 8. Do NOT give 7 or lower unless you can explicitly list multiple important
ideas that are completely absent. Condensed phrasing, paraphrase, or shorter wording are NOT
reasons to lower the score — interpretation is always shorter than the source.

Only add an item to missing_content if an important idea or fact is genuinely and completely absent.

TASK 3 — PRONUNCIATION FLAGS:
The uncertain words listed above are words Whisper was not confident about.
IMPORTANT: low ASR confidence does NOT mean the word was mispronounced — ASR is often uncertain
about rare words, technical terms, proper nouns, or words with silent letters even when spoken
correctly. Only flag a word as a pronunciation issue if you have CLEAR EVIDENCE the student said
it incorrectly — not just because the confidence score is low.
NEVER flag these as pronunciation errors:
- French silent final letters (s, t, d, x, p, g, ent) — they are CORRECT French pronunciation.
  "délégués" sounds identical to "délégué" — this is correct, not a mistake.
- Correct target-language renderings of proper nouns or acronyms.
- Words that were simply unfamiliar to the ASR engine.
Only report genuine mispronunciations where the student clearly said the wrong sounds.

TASK 4 — FLUENCY ISSUES IN {target_language}:
- Hesitations: vocal fillers only — آ، يعني، أقصد (Arabic) / euh, heu (French) / um, uh, er (English),
  plus words cut mid-way and restarted. Discourse words (donc, alors, en fait, like, you know) are
  legitimate speech — never hesitations.
- Repetitions: words said twice in a row
- False starts: ONLY a genuinely abandoned multi-word phrase — the student starts a sentence,
  abandons it entirely, and says something different (e.g. "The delegates have... We must act now.").
  A single cut word, a filler, or a repeated word is NOT a false start — those are hesitations
  or repetitions and must not be duplicated here. If there is no clearly abandoned phrase in the
  transcript, return an EMPTY false_starts list. Never invent one.
- Auto-corrections: student corrects themselves mid-sentence
- Lapsus linguae: wrong word slipped out

TASK 5 — LANGUAGE QUALITY IN {target_language}:
Grammar errors in the INTERPRETATION language (not the source):
- Arabic: wrong case endings (إعراب), verb agreement, wrong تشكيل
- French: gender agreement, wrong tense, wrong preposition. Do not penalize silent final plural "s"
  inferred only from ASR spelling.
- English: tense, subject-verb agreement
STRICT EXCLUSIONS — do NOT flag any of the following as language errors:
- Capitalization differences (e.g. "conférence des parties" vs "Conférence des Parties") — capitalization is a typographic convention, not a spoken-language error.
- Official proper-noun casing for UN bodies, treaty names, or institutional titles — if the student said the right words, do not flag casing.
- Stylistic or register variation where the meaning is the same (e.g. formal vs informal equivalents of the same correct idea).
- Paraphrases that convey the correct meaning even if worded differently from the source.
Do NOT flag number formatting as a language error (e.g. "8,8 milliards" is correct French —
French uses a comma as the decimal separator, English uses a period). Whether the NUMBER VALUE
itself is correct is judged separately in TASK 10, not here.

TASK 6 — NUMBERS AND DATES:
Extract every number, percentage, date, statistic from the SOURCE speech.
Check each one in the STUDENT interpretation. Flag wrong or missing numbers.

TASK 7 — TERMINOLOGY:
Key domain-specific terms from the source — were they rendered with the correct equivalent in the target language?

TASK 8 — PAUSES & FLOW:
{silence_count} pause(s) longer than 2 seconds were detected: {silence_examples}
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

CRITICAL — fill student_said correctly:
- If the student said a DIFFERENT number in place of the correct one (e.g., said 100 instead of 98),
  set student_said to what they actually said ("100") — do NOT leave student_said empty in this case.
- Only set student_said to "" or null if the number was completely omitted with no replacement.
- This distinction is essential: "said 100 instead of 98" is a substitution error, not a missing number.

CRITICAL — do NOT flag format-only differences as errors:
- Date word order differs between languages: "29 June 2026", "June 29, 2026" and "٢٩ يونيو ٢٠٢٦"
  are the SAME date → correct.
- Decimal separators differ: "8.8 billion" (EN) = "8,8 milliards" (FR) → correct.
- Arabic-Indic digits (٢٠٢٦) and Western digits (2026) are the same number → correct.
Only flag a number/date when the VALUE the listener hears is actually different.

TASK 11 — PRONUNCIATION IN {target_language}:
LOW-CONFIDENCE WORDS the speech recognizer was unsure about: {uncertain_words}
CRITICAL: low ASR confidence ≠ mispronunciation. ASR is routinely uncertain about rare words,
technical terms, proper nouns, and words with silent letters even when spoken perfectly correctly.
Do NOT flag a word as mispronounced just because ASR scored it low.
For French: silent final letters (s, t, d, x, p, ent) are CORRECT — "partenaires" and
"partenaire" sound identical; this is correct French pronunciation, not an error.
Only give pronunciation feedback when you have clear evidence the student said the sounds wrong.
Give specific, actionable pronunciation feedback for {target_language}:
- Arabic: تشكيل/إعراب (case endings), emphatic vs plain consonants (ص/س، ض/د، ط/ت، ظ/ذ، ق/ك),
  hamza ء placement, تاء مربوطة pronunciation, vowel length (مد/قصر)
- French: nasal vowels, liaison, silent final letters, gender-driven endings affecting sound
- English: word stress, "th" sounds (θ/ð), vowel reduction in unstressed syllables
For each low-confidence word above, explain the likely mispronunciation and give the correct way to say it.

TASK 12 — PROPER NOUNS (people, organizations, places, treaties):
{proper_nouns_block}
For EVERY proper noun in the source, classify the student's rendering as one of:
- "correct": the name is present and recognizably right in {target_language}. A legitimate
  target-language form counts as correct (e.g. "United Nations" → "ONU" or "الأمم المتحدة";
  transliteration into Arabic script is correct rendering, NOT distortion).
  Official target-language abbreviations are always correct: ESCWA → CESAO (FR), SDGs → ODD (FR),
  WHO → OMS (FR), UNDP → PNUD (FR). Capitalisation differences NEVER make a name "distorted".
  A correct translation or paraphrase of a name is "correct", not "distorted".
- "distorted": the name appears but clearly MISPRONOUNCED or garbled — wrong syllables, wrong
  letters, clearly altered sound (e.g. "Mobuto Seko" instead of "Mobutu Sese Seko").
  Do NOT use "distorted" for: capitalisation variants, accepted target-language equivalents,
  bilingual dual abbreviations (e.g. "CESAO-ESCWA"), or stylistic name variants with correct meaning.
  Hyphenation differences are NEVER errors: "Jean-Pierre" vs "Jean Pierre", "New-York" vs "New York",
  or any hyphen-vs-space variant must be marked "correct", not "distorted".
  In a spoken exam a distorted name means the student got the sounds/syllables wrong — quote exactly
  what the recognizer heard so the student can compare.
- "missing": the name was omitted entirely.
Names are identity-critical in interpretation — a distorted head-of-state or organization name
can be a diplomatic incident. Flag every genuine mispronunciation and omission.

Give overall_score 0-10 and coverage_score 0-10.
STRICTNESS APPLIES TO overall_score ONLY. coverage_score follows the MANDATORY rubric in TASK 2:
empty missing_content = coverage 9-10, no exceptions. A complete interpretation gets full coverage
credit even when other error types (grammar, pronunciation, hesitations) lower the overall_score.
Be strict on overall_score — most student interpretations score 4–7:
- 9-10: Exceptional — virtually no errors, complete coverage, professional fluency
- 7-8: Good — only 1-2 minor errors, no significant meaning loss
- 5-6: Acceptable — several errors but core meaning mostly preserved
- 3-4: Weak — multiple mistranslations or significant information loss
- 0-2: Very poor — major errors, incomplete, or incomprehensible
If you found 3+ translation errors or missing_content items, overall_score cannot exceed 6.

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
  "proper_nouns": [
    {{"source_name": "name in the source", "student_said": "what the recognizer heard", "status": "correct", "note": "short comment; for distorted names explain the likely mispronunciation"}}
  ],
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

_NAME_CONNECTORS = {'of', 'de', 'du', 'des', 'la', 'le', 'el', 'al', 'bin', 'ben', 'van', 'von', 'ibn'}


def extract_proper_nouns(text: str, max_names: int = 15) -> list[str]:
    """
    Heuristic proper-noun extraction for Latin-script sources (EN/FR):
    capitalized word runs (skipping sentence-initial words) and acronyms.
    Arabic has no capitalization — for Arabic sources the LLM extracts
    the names itself (the prompt instructs it to).
    """
    text = str(text or '')
    if not re.search(r'[A-Za-z]', text):
        return []

    names: list[str] = []
    seen = set()

    def flush(run: list[str]):
        while run and run[-1].lower() in _NAME_CONNECTORS:
            run.pop()
        if not run:
            return
        name = ' '.join(run)
        key = name.casefold()
        if key not in seen and len(name) > 2:
            seen.add(key)
            names.append(name)

    for sentence in re.split(r'(?<=[.!?])\s+', text):
        words = sentence.split()
        run: list[str] = []
        for index, raw in enumerate(words):
            token = raw.strip('.,;:!?"“”«»()[]')
            is_name_word = bool(re.fullmatch(r"[A-ZÀ-Þ][\w'’à-þ-]+|[A-Z]{2,}s?", token))
            is_connector = token.lower() in _NAME_CONNECTORS
            if is_name_word and (index > 0 or len(token) > 1 and token.isupper()):
                run.append(token)
            elif is_connector and run:
                run.append(token)
            else:
                flush(run)
                run = []
        flush(run)

    return names[:max_names]


def build_proper_nouns_block(source_script: str) -> str:
    """Feed the detected source names to the evaluator so each one is verified."""
    names = extract_proper_nouns(source_script)
    if names:
        return ('\nPROPER NOUNS detected in the source — verify EVERY one of them in the '
                'student\'s rendering (TASK 12): ' + '; '.join(names) + '\n')
    return ('\nThe source may contain proper nouns (people, organizations, places, treaties) — '
            'extract them yourself and verify each one in the student\'s rendering (TASK 12).\n')


def build_glossary_block(glossary_raw: str) -> str:
    """
    Build the approved-glossary section of the evaluation prompt (cahier des
    charges request: the student reviews/corrects the glossary BEFORE recording
    so terminology errors are judged against the approved equivalents).
    """
    if not glossary_raw:
        return ''
    try:
        entries = json.loads(glossary_raw)
    except (ValueError, TypeError):
        return ''
    if not isinstance(entries, list) or not entries:
        return ''

    lines = []
    for entry in entries[:30]:
        if not isinstance(entry, dict):
            continue
        term = str(entry.get('term', '') or '').strip()
        ar = str(entry.get('arabic', '') or entry.get('ar', '') or '').strip()
        fr = str(entry.get('french', '') or entry.get('fr', '') or '').strip()
        en = str(entry.get('english', '') or entry.get('en', '') or '').strip()
        parts = [p for p in [term, f'AR: {ar}' if ar else '', f'FR: {fr}' if fr else '', f'EN: {en}' if en else ''] if p]
        if parts:
            lines.append('- ' + ' | '.join(parts))
    if not lines:
        return ''

    return (
        '\nAPPROVED GLOSSARY (reviewed by the student BEFORE recording — these are the '
        'REQUIRED terminology equivalents; in TASK 7 judge the student\'s terminology '
        'against these exact equivalents and flag every deviation):\n'
        + '\n'.join(lines) + '\n'
    )


def format_silences_for_prompt(silences: list) -> str:
    """Format silence examples for the LLM, excluding leading preparation time."""
    delivery_silences = [s for s in (silences or []) if not is_leading_silence(s)]
    leading = [s for s in (silences or []) if is_leading_silence(s)]
    parts = '; '.join(
        f'{sl["duration_seconds"]}s' + (f' after "{sl["after_text"]}"' if sl.get('after_text') else '')
        for sl in delivery_silences[:5]
    )
    note = ''
    if leading:
        lead_secs = max(float(s.get('duration_seconds', 0) or 0) for s in leading)
        note = (f' (note: the student also took {lead_secs}s of preparation time before '
                'starting to speak — this is normal and must NOT be judged as a delivery pause)')
    return (parts or 'none found automatically') + note


def transcribe_eval_with_groq(audio_path: str, language: str, prompt: str):
    """
    Transcribe with Groq whisper-large-v3 requesting WORD-level timestamps
    (timestamp_granularities) — large-v3 recognizes Arabic far better than the
    local medium model and returns in seconds instead of minutes. Calls the
    REST API directly so the installed SDK version does not matter.
    Returns None on any failure so the caller falls back to local ASR.
    """
    try:
        from utils.groq_client import get_groq_key
        key = get_groq_key()
        if not key:
            return None

        import requests as _requests
        with open(audio_path, 'rb') as fh:
            resp = _requests.post(
                'https://api.groq.com/openai/v1/audio/transcriptions',
                headers={'Authorization': f'Bearer {key}'},
                files={'file': (os.path.basename(audio_path), fh)},
                data=[
                    ('model', 'whisper-large-v3'),
                    ('language', language),
                    ('response_format', 'verbose_json'),
                    ('timestamp_granularities[]', 'word'),
                    ('timestamp_granularities[]', 'segment'),
                    ('prompt', prompt[:400]),
                ],
                timeout=120,
            )
        if not resp.ok:
            print(f'[Module D] Groq eval ASR failed ({resp.status_code}: {resp.text[:120]}) — using local model')
            return None

        data = resp.json()
        raw_segments = data.get('segments') or []
        raw_words = data.get('words') or []

        segments = []
        for seg in raw_segments:
            seg_text = str(seg.get('text', '')).strip()
            if not seg_text or seg_text[0] in '[(':
                continue
            segments.append({
                'start': round(float(seg.get('start', 0) or 0), 2),
                'end':   round(float(seg.get('end', 0) or 0), 2),
                'text':  seg_text,
                'words': [],
            })

        # Words arrive as a flat list; attach each to its segment by time so
        # the silence/repetition/hesitation detectors work unchanged.
        # The cloud API gives no per-word confidence → 1.0 neutral score.
        word_scores = []
        for w in raw_words:
            token = str(w.get('word', '')).strip()
            if not token:
                continue
            start = round(float(w.get('start', 0) or 0), 2)
            end = round(float(w.get('end', 0) or 0), 2)
            entry = {'word': token, 'start': start, 'end': end, 'probability': 1.0}
            for seg in segments:
                if seg['start'] - 0.05 <= start < seg['end'] + 0.05:
                    seg['words'].append(entry)
                    break
            else:
                if segments:
                    segments[-1]['words'].append(entry)
            word_scores.append({'word': token, 'start': start, 'end': end, 'score': 1.0, 'grade': 'good'})

        if not segments and not word_scores:
            return None

        return {
            'segments': segments,
            'word_scores': word_scores,
            'segment_text': ' '.join(s['text'] for s in segments).strip(),
            'language': str(data.get('language', language) or language),
            'duration': round(float(data.get('duration', 0) or 0), 1),
        }
    except Exception as exc:
        print(f'[Module D] Groq eval ASR error: {exc} — using local model')
        return None


module_d_bp = Blueprint('module_d', __name__)


# ── Error detection (algorithmic — no LLM calls, always free) ────────────────

# ── Hesitation word lists — GENUINE vocal fillers only.
# Discourse words that are legitimate speech ("donc", "alors", "like",
# "en fait", "you know") must NEVER be flagged: in a formal interpretation
# they are normal vocabulary, and flagging them buries real hesitations.
HESITATION_PATTERNS = {
    'ar': [
        r'\bآ+\b', r'\bإ+\b', r'\bأممم+\b', r'\bممم+\b', r'\bيعني\b', r'\bأقصد\b',
        r'\beuh+\b', r'\bheu+\b', r'\bum+\b', r'\buh+\b', r'\bhmm+\b', r'\bhm+\b',
    ],
    'fr': [r'\beuh+\b', r'\bheu+\b', r'\bhm+\b', r'\bhum+\b'],
    'en': [r'\bum+\b', r'\buh+\b', r'\ber+m?\b', r'\bhmm+\b', r'\bhm+\b'],
}

HESITATION_FILLERS = {
    'ar': {
        'آ', 'إ', 'أقصد', 'يعني', 'آآ', 'إإ', 'أممم', 'ممم', 'اممم',
        'euh', 'heu', 'um', 'uh', 'hmm', 'hm', 'erm', 'er',
    },
    'fr': {
        'euh', 'heu', 'euuh', 'euhm', 'hum', 'hm', 'hmm',
    },
    'en': {
        'um', 'umm', 'uh', 'uhh', 'er', 'erm', 'hmm', 'hm', 'mm',
    },
}

# Stalling phrases only — phrases a speaker says while searching for words.
# Normal discourse phrases ("en fait", "you know", "i mean") are NOT here.
HESITATION_PHRASES = {
    'fr': ['comment dire', 'comment dirais je'],
    'en': [],
    'ar': [],
}


def normalize_hesitation_token(text: str) -> str:
    return re.sub(r"^[^\w]+|[^\w]+$", '', str(text or '').strip().lower(), flags=re.UNICODE)

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
    """Detect filler words and hesitation phrases in transcript text."""
    filler_set = HESITATION_FILLERS.get(language, HESITATION_FILLERS['en'])
    if language == 'ar':
        filler_set = HESITATION_FILLERS['ar'] | HESITATION_FILLERS['fr'] | HESITATION_FILLERS['en']

    found = []
    for match in re.finditer(r'\w+', full_text or '', flags=re.IGNORECASE | re.UNICODE):
        token = normalize_hesitation_token(match.group())
        if token in filler_set or re.fullmatch(r'(u+h+|u+m+|e+u+h+|h+m+|m+m+|آ+|إ+|[اأ]م{2,}|م{3,})', token):
            found.append({'word': match.group(), 'at_char': match.start(), 'source': 'text'})

    normalized_text = re.sub(r'[^\w]+', ' ', str(full_text or '').lower(), flags=re.UNICODE)
    phrase_languages = ['ar', 'fr', 'en'] if language == 'ar' else [language]
    for phrase_language in phrase_languages:
        for phrase in HESITATION_PHRASES.get(phrase_language, []):
            search_phrase = re.sub(r'[^\w]+', ' ', phrase.lower(), flags=re.UNICODE).strip()
            if not search_phrase:
                continue
            for match in re.finditer(rf'\b{re.escape(search_phrase)}\b', normalized_text, flags=re.IGNORECASE):
                found.append({'word': phrase, 'at_char': match.start(), 'source': 'phrase'})

    seen = set()
    unique = []
    for item in found:
        key = (item['word'].lower(), item.get('at_char'))
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique

def normalize_repetition_word(text: str) -> str:
    return re.sub(r'[^\w]', '', str(text or '').strip().casefold(), flags=re.UNICODE)


def build_repetition_hotwords(source_script: str, language: str = 'en') -> str:
    """
    Bias faster-whisper toward words that appear in the source speech.
    English ASR tends to collapse accidental repeats, so repeating source terms
    in the hotword list helps preserve cases like "climate climate".
    """
    common_words = {
        'en': {
            'the', 'a', 'an', 'and', 'or', 'but', 'to', 'of', 'in', 'on', 'for', 'from',
            'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'it', 'this', 'that',
            'these', 'those', 'as', 'at', 'we', 'they', 'he', 'she', 'you', 'i',
        },
        'fr': {
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'd', 'et', 'ou', 'mais',
            'a', 'au', 'aux', 'en', 'dans', 'pour', 'par', 'avec', 'est', 'sont', 'ce',
            'cette', 'ces', 'nous', 'vous', 'ils', 'elles',
        },
        'ar': set(),
    }
    base = [
        'um', 'uh', 'er', 'erm', 'hmm', 'euh', 'heu',
        'repeated', 'repeated', 'word', 'word',
    ]
    stopwords = common_words.get(language, common_words['en'])
    seen = set()
    source_terms = []
    for match in re.finditer(r'\w+', source_script or '', flags=re.UNICODE):
        token = normalize_repetition_word(match.group(0))
        if len(token) < 4 or token in stopwords or token in seen:
            continue
        seen.add(token)
        source_terms.extend([token, token])
        if len(source_terms) >= 80:
            break
    return ' '.join(base + source_terms)


def repetition_compare_key(text: str, language: str = 'ar') -> str:
    """Normalize a word for repetition comparison without changing display text."""
    import unicodedata

    token = normalize_repetition_word(text)
    token = unicodedata.normalize('NFKD', token)
    token = ''.join(char for char in token if not unicodedata.combining(char))

    # French plural markers are often silent; strip trailing 's' only for French
    # so English words like "goes"/"go" or "days"/"day" are not conflated.
    if language == 'fr' and len(token) > 3 and token.endswith('s'):
        token = token[:-1]
    return token


def words_are_repetition_equivalent(first: str, second: str, language: str = 'ar') -> bool:
    first_key = repetition_compare_key(first, language)
    second_key = repetition_compare_key(second, language)
    return bool(first_key and first_key == second_key)


def detect_repetitions_from_text(full_text: str, language: str = 'ar') -> list:
    """Detect immediate repeated words or repeated adjacent short phrases."""
    skip_words = _SHORT_PARTICLES.get(language, set())
    words = []
    for match in re.finditer(r'\w+', full_text or '', flags=re.UNICODE):
        word = normalize_repetition_word(match.group(0))
        if word and word not in skip_words:
            words.append({
                'word': word,
                'key': repetition_compare_key(word, language),
                'position': len(words),
                'char': match.start(),
            })
    repetitions = []

    for i in range(len(words) - 1):
        if words_are_repetition_equivalent(words[i]['word'], words[i + 1]['word'], language):
            repetitions.append({
                'word': words[i]['word'],
                'position': words[i]['position'],
                'at_char': words[i]['char'],
                'gap_words': 1,
                'source': 'text_immediate',
            })

    for phrase_len in (2, 3):
        for i in range(len(words) - (phrase_len * 2) + 1):
            first = [item['key'] for item in words[i:i + phrase_len]]
            second = [item['key'] for item in words[i + phrase_len:i + (phrase_len * 2)]]
            # Require at least one substantial word (≥5 chars) to avoid false positives
            # from short content words that happen to appear twice in sequence
            if first == second and any(len(k) >= 5 for k in first):
                repetitions.append({
                    'word': ' '.join(item['word'] for item in words[i:i + phrase_len]),
                    'position': words[i]['position'],
                    'at_char': words[i]['char'],
                    'gap_words': phrase_len,
                    'source': 'text_phrase_immediate',
                })

    return repetitions


def detect_long_silences(segments: list, threshold_seconds: float = 2.0) -> list:
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

    ordered_segments = sorted(segments, key=lambda seg: seg.get('start', 0))

    if ordered_segments[0].get('start', 0) >= threshold_seconds:
        silences.append({
            'at_seconds': 0.0,
            'duration_seconds': round(ordered_segments[0].get('start', 0), 1),
            'after_text': '[start of recording]',
            'type': 'leading'
        })

    for i in range(len(ordered_segments) - 1):
        gap = round(ordered_segments[i + 1].get('start', 0) - ordered_segments[i].get('end', 0), 2)
        if gap >= threshold_seconds:
            silences.append({
                'at_seconds': round(ordered_segments[i].get('end', 0), 1),
                'duration_seconds': gap,
                'after_text': ordered_segments[i].get('text', '')[-60:].strip(),
                'type': 'segment_gap'
            })

    words = []
    for seg in ordered_segments:
        for word in seg.get('words', []) or []:
            start = word.get('start')
            end = word.get('end')
            if start is None or end is None:
                continue
            words.append({
                'word': str(word.get('word', '')).strip(),
                'start': float(start),
                'end': float(end),
            })

    words.sort(key=lambda item: item['start'])
    word_gap_threshold = threshold_seconds
    for i in range(len(words) - 1):
        gap = round(words[i + 1]['start'] - words[i]['end'], 2)
        if gap >= word_gap_threshold:
            silences.append({
                'at_seconds': round(words[i]['end'], 1),
                'duration_seconds': gap,
                'after_text': words[i]['word'],
                'type': 'word_gap',
            })

    deduped = []
    seen = set()
    for silence in sorted(silences, key=lambda item: (item['at_seconds'], item['duration_seconds'])):
        key = (round(silence['at_seconds'], 1), round(silence['duration_seconds'], 1))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(silence)
    return deduped


def decode_audio_mono(audio_path: str, target_rate: int = 16000):
    """Decode audio to mono float samples using PyAV, already required by faster-whisper."""
    try:
        import av
        import numpy as np

        container = av.open(audio_path)
        stream = next((s for s in container.streams if s.type == 'audio'), None)
        if stream is None:
            return None, target_rate

        resampler = av.AudioResampler(format='s16', layout='mono', rate=target_rate)
        chunks = []
        for frame in container.decode(stream):
            resampled = resampler.resample(frame)
            if not isinstance(resampled, list):
                resampled = [resampled]
            for audio_frame in resampled:
                array = audio_frame.to_ndarray()
                if array.size:
                    chunks.append(array.reshape(-1).astype('float32') / 32768.0)
        container.close()

        if not chunks:
            return None, target_rate
        return np.concatenate(chunks), target_rate
    except Exception as exc:
        print(f'[Module D] Audio decode failed: {exc}')
        return None, target_rate


def audio_dbfs(samples) -> float:
    """Approximate dBFS for float samples in [-1, 1]."""
    import numpy as np
    if samples is None or len(samples) == 0:
        return float('-inf')
    rms = float(np.sqrt(np.mean(np.square(samples))))
    if rms <= 0:
        return float('-inf')
    return 20.0 * float(np.log10(rms))


def detect_audio_silences(audio_path: str, threshold_ms: int = 2000) -> list:
    """Detect quiet gaps directly from decoded audio energy."""
    try:
        import numpy as np

        samples, sample_rate = decode_audio_mono(audio_path)
        if samples is None or len(samples) == 0:
            return []

        global_db = audio_dbfs(samples)
        if global_db == float('-inf'):
            return []

        silence_thresh = max(global_db - 14, -42)
        window_ms = 20
        window_size = max(1, int(sample_rate * window_ms / 1000))
        min_windows = max(1, int(threshold_ms / window_ms))

        silent_windows = []
        for start in range(0, len(samples), window_size):
            chunk = samples[start:start + window_size]
            silent_windows.append(audio_dbfs(chunk) < silence_thresh)

        ranges = []
        start_window = None
        for index, is_silent in enumerate(silent_windows + [False]):
            if is_silent and start_window is None:
                start_window = index
            elif not is_silent and start_window is not None:
                if index - start_window >= min_windows:
                    start_ms = start_window * window_ms
                    end_ms = min(index * window_ms, int(len(samples) / sample_rate * 1000))
                    ranges.append((start_ms, end_ms))
                start_window = None

        return [
            {
                'at_seconds': round(start / 1000, 1),
                'duration_seconds': round((end - start) / 1000, 1),
                'after_text': '[audio silence]',
                'type': 'audio_silence',
            }
            for start, end in ranges
            if (end - start) >= threshold_ms
        ]
    except Exception as exc:
        print(f'[Module D] Audio silence detection failed: {exc}')
        return []


def get_word_timing_sequence(segments: list) -> list:
    """Return sorted ASR word timings with empty tokens removed."""
    words = []
    for seg in segments or []:
        for word in seg.get('words', []) or []:
            token = str(word.get('word', '')).strip()
            start = word.get('start')
            end = word.get('end')
            if not token or start is None or end is None:
                continue
            words.append({
                'word': token,
                'start': float(start),
                'end': float(end),
            })
    return sorted(words, key=lambda item: item['start'])


def build_transcript_from_word_timestamps(segments: list) -> str:
    """
    Build a verbatim-ish transcript from ASR word timestamps.
    faster-whisper segment.text can clean up repeated words, while segment.words
    often still contains the repeated tokens needed for evaluation.
    """
    words = []
    for item in get_word_timing_sequence(segments):
        token = str(item.get('word', '')).strip()
        if token:
            words.append(token)
    return re.sub(r'\s+', ' ', ' '.join(words)).strip()


def detect_audio_filled_pauses(audio_path: str, segments: list, min_gap_seconds: float = 0.30, max_gap_seconds: float = 2.0) -> list:
    """
    Detect likely filled pauses from the recording when ASR omits fillers.
    A gap between recognized words that still contains voiced audio is usually
    a filler ("euhhh") the recognizer skipped. min_gap 0.30 s: anything shorter
    is normal coarticulation/breath between words, not a hesitation. max_gap
    2.0 s: a long drawn-out "euhhhhh" still counts (beyond that it overlaps
    with the silence detector).
    """
    try:
        words = get_word_timing_sequence(segments)
        if len(words) < 2:
            return []

        samples, sample_rate = decode_audio_mono(audio_path)
        if samples is None or len(samples) == 0:
            return []

        global_db = audio_dbfs(samples)
        if global_db == float('-inf'):
            return []

        # -18 dB below global level: soft "euhhh" spoken quieter than normal
        # speech must still register as voiced.
        silence_thresh = max(global_db - 18, -45)
        candidates = []

        for previous, current in zip(words, words[1:]):
            gap = current['start'] - previous['end']
            if gap < min_gap_seconds or gap > max_gap_seconds:
                continue

            start_index = max(0, int(previous['end'] * sample_rate))
            end_index = min(len(samples), int(current['start'] * sample_rate))
            chunk = samples[start_index:end_index]
            if len(chunk) < int(min_gap_seconds * sample_rate):
                continue

            # Voiced but unrecognized audio inside a short word gap is a likely filler.
            if audio_dbfs(chunk) > silence_thresh + 1:
                candidates.append({
                    'word': '[filled pause]',
                    'at_seconds': round(previous['end'], 1),
                    'duration_seconds': round(gap, 2),
                    'after_text': previous['word'],
                    'confidence': None,
                    'source': 'audio_gap',
                })

        return candidates
    except Exception as exc:
        print(f'[Module D] Audio filled-pause detection failed: {exc}')
        return []


def detect_cut_words_from_audio(audio_path: str,
                                 min_burst_ms: int = 80,
                                 max_burst_ms: int = 350,
                                 min_gap_ms: int = 60,
                                 max_gap_ms: int = 700) -> list:
    """
    Detect mid-word interruptions (cut words) directly from audio energy.

    Pattern looked for:
      SHORT voiced burst (80–350 ms)  →  silence gap (60–700 ms)  →  longer voiced segment

    This catches the case where the student starts a word, stops mid-syllable,
    and restarts — even when the ASR removes the partial word entirely from the
    transcript (which Groq whisper-large-v3 almost always does). These count
    as hesitations (D5 disfluency category).

    Thresholds are deliberately conservative (min burst 80 ms, restart must be
    a solid speech segment) so lip noise and breaths are not flagged.

    Returns items in the same shape as hesitation_words so they merge cleanly.
    """
    try:
        import numpy as np

        samples, sample_rate = decode_audio_mono(audio_path)
        if samples is None or len(samples) == 0:
            return []

        global_db = audio_dbfs(samples)
        if global_db == float('-inf'):
            return []

        voiced_thresh = max(global_db - 14, -42)
        window_ms  = 10
        win_size   = max(1, int(sample_rate * window_ms / 1000))

        # Label each 10-ms window as voiced/silent
        voiced_flags = [
            audio_dbfs(samples[s:s + win_size]) >= voiced_thresh
            for s in range(0, len(samples), win_size)
        ]

        # Merge consecutive same-label windows into segments
        segs: list[tuple[str, int, int]] = []   # (kind, start_ms, end_ms)
        if not voiced_flags:
            return []
        kind   = 'voiced' if voiced_flags[0] else 'silent'
        t_start = 0
        for i, v in enumerate(voiced_flags[1:], start=1):
            cur = 'voiced' if v else 'silent'
            if cur != kind:
                segs.append((kind, t_start * window_ms, i * window_ms))
                kind    = cur
                t_start = i
        segs.append((kind, t_start * window_ms, len(voiced_flags) * window_ms))

        cut_words = []
        # Look for: voiced(short) → silent → voiced(longer)
        for i in range(len(segs) - 2):
            s0, s1, s2 = segs[i], segs[i + 1], segs[i + 2]
            if s0[0] != 'voiced' or s1[0] != 'silent' or s2[0] != 'voiced':
                continue

            burst_ms = s0[2] - s0[1]
            gap_ms   = s1[2] - s1[1]
            next_ms  = s2[2] - s2[1]

            if not (min_burst_ms <= burst_ms <= max_burst_ms):
                continue
            if not (min_gap_ms <= gap_ms <= max_gap_ms):
                continue
            # The restart must be a solid speech segment, meaningfully longer
            # than the interrupted burst — filters clicks/breaths.
            if next_ms < max(300, burst_ms * 1.2):
                continue

            cut_words.append({
                'word':             '[cut word]',
                'at_seconds':       round(s0[1] / 1000, 1),
                'duration_seconds': round(burst_ms / 1000, 3),
                'confidence':       1.0,
                'source':           'audio_cut_word',
            })

        return cut_words
    except Exception as exc:
        print(f'[Module D] Audio cut-word detection failed: {exc}')
        return []


def merge_silence_reports(*reports: list) -> list:
    """Merge overlapping/near-duplicate silence detections from ASR and audio."""
    merged = []
    for report in reports:
        for silence in report or []:
            at_seconds = float(silence.get('at_seconds', 0) or 0)
            duration = float(silence.get('duration_seconds', 0) or 0)
            existing = next(
                (
                    item for item in merged
                    if abs(float(item.get('at_seconds', 0) or 0) - at_seconds) <= 0.5
                ),
                None,
            )
            if existing:
                if duration > float(existing.get('duration_seconds', 0) or 0):
                    existing['duration_seconds'] = round(duration, 1)
                existing['type'] = f"{existing.get('type', 'silence')}+{silence.get('type', 'silence')}"
                if existing.get('after_text') in ['', '[audio silence]'] and silence.get('after_text'):
                    existing['after_text'] = silence.get('after_text')
            else:
                merged.append(dict(silence))

    return sorted(merged, key=lambda item: item.get('at_seconds', 0))


def detect_repetitions(segments: list, language: str = 'ar') -> list:
    """
    Detect immediate repeated words and adjacent repeated short phrases.
    """
    skip_words = _SHORT_PARTICLES.get(language, set())
    all_words = []
    for seg in segments:
        for w in seg.get('words', []):
            clean = normalize_repetition_word(w.get('word', ''))
            if clean and clean not in skip_words:
                all_words.append({
                    'word': clean,
                    'key': repetition_compare_key(clean, language),
                    'start': w.get('start', 0),
                })

    if not all_words:
        return []

    repetitions = []
    i = 0
    while i < len(all_words) - 1:
        word = all_words[i]['word']
        if words_are_repetition_equivalent(word, all_words[i + 1]['word'], language):
            repetitions.append({
                'word': word,
                'at_seconds': round(all_words[i]['start'], 1),
                'second_occurrence': round(all_words[i + 1]['start'], 1),
                'gap_words': 1,
                'source': 'word_immediate'
            })
            i += 2
            continue
        i += 1

    phrase_used_positions = set()
    for phrase_len in (2, 3):
        for i in range(len(all_words) - (phrase_len * 2) + 1):
            positions = set(range(i, i + (phrase_len * 2)))
            if phrase_used_positions & positions:
                continue
            first = [item['key'] for item in all_words[i:i + phrase_len]]
            second = [item['key'] for item in all_words[i + phrase_len:i + (phrase_len * 2)]]
            # Mirror the text-detector's guard: require at least one substantial word
            if first == second and any(len(k) >= 5 for k in first):
                repetitions.append({
                    'word': ' '.join(item['word'] for item in all_words[i:i + phrase_len]),
                    'at_seconds': round(all_words[i]['start'], 1),
                    'second_occurrence': round(all_words[i + phrase_len]['start'], 1),
                    'gap_words': phrase_len,
                    'source': 'word_phrase_immediate'
                })
                phrase_used_positions.update(positions)

    return repetitions


def merge_repetition_reports(*reports: list) -> list:
    """Merge timing-window, word-level, and text-level repetition reports.

    Strategy:
    - Deduplicate word-level (timestamped) items by (word, time) within 0.8s.
    - Text-level items that have timestamps use the same proximity check.
    - Text-only items (no at_seconds) are treated as fallback: skip if the
      same word already appears in merged results (timing/word found it).
    """
    word_level = list(reports[0] or []) if reports else []
    text_level = []
    for report in reports[1:]:
        text_level.extend(report or [])

    merged = []

    for item in word_level:
        word = normalize_repetition_word(str(item.get('word', '')))
        if not word:
            continue
        at_s = round(float(item.get('at_seconds') or 0), 1)
        if any(normalize_repetition_word(str(ex.get('word', ''))) == word
               and abs(float(ex.get('at_seconds') or 0) - at_s) < 0.8
               for ex in merged):
            continue
        merged.append(item)

    words_in_merged = {normalize_repetition_word(str(ex.get('word', ''))) for ex in merged}

    for item in text_level:
        word = normalize_repetition_word(str(item.get('word', '')))
        if not word:
            continue
        has_time = item.get('at_seconds') is not None
        if has_time:
            at_s = round(float(item['at_seconds']), 1)
            if any(normalize_repetition_word(str(ex.get('word', ''))) == word
                   and abs(float(ex.get('at_seconds') or 0) - at_s) < 0.8
                   for ex in merged):
                continue
        else:
            # Text-only fallback: skip entirely if timing/word detection already found this word
            if word in words_in_merged:
                continue
        merged.append(item)
        words_in_merged.add(word)

    return merged


def detect_hesitation_words(segments: list, language: str = 'ar') -> list:
    """Detect filler / hesitation words from word-level ASR timestamps."""
    filler_set = HESITATION_FILLERS.get(language, HESITATION_FILLERS['en'])
    if language == 'ar':
        filler_set = HESITATION_FILLERS['ar'] | HESITATION_FILLERS['fr'] | HESITATION_FILLERS['en']

    found = []
    for seg in segments:
        for w in seg.get('words', []) or []:
            clean = normalize_hesitation_token(w.get('word', ''))
            if clean in filler_set or re.fullmatch(r'(u+h+|u+m+|e+u+h+|h+m+|m+m+|آ+|إ+|[اأ]م{2,}|م{3,})', clean):
                found.append({
                    'word': str(w.get('word', '')).strip(),
                    'at_seconds': round(w.get('start', 0), 1),
                    'confidence': round(w.get('probability', 1.0), 3),
                    'source': 'word'
                })
    return found


def merge_hesitation_reports(*reports: list) -> list:
    """Merge word-level and transcript-text hesitation detections without double counting."""
    word_level = list(reports[0] or []) if reports else []
    text_level = []
    for report in reports[1:]:
        text_level.extend(report or [])

    merged = []
    seen = set()
    word_counts = {}

    for item in word_level:
        word = str(item.get('word', '')).strip()
        if not word:
            continue
        normalized = normalize_hesitation_token(word)
        time_bucket = round(float(item.get('at_seconds', 0) or 0), 1) if item.get('at_seconds') is not None else None
        key = (normalized, time_bucket)
        if key in seen:
            continue
        seen.add(key)
        word_counts[normalized] = word_counts.get(normalized, 0) + 1
        merged.append(item)

    skipped_text_counts = {}
    for item in text_level:
        word = str(item.get('word', '')).strip()
        if not word:
            continue
        normalized = normalize_hesitation_token(word)
        if skipped_text_counts.get(normalized, 0) < word_counts.get(normalized, 0):
            skipped_text_counts[normalized] = skipped_text_counts.get(normalized, 0) + 1
            continue
        char_bucket = item.get('at_char')
        key = (normalized, char_bucket)
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def detect_low_confidence_words(segments: list, threshold: float = 0.6) -> list:
    """
    Flag words Whisper was uncertain about (probability < threshold).
    These often correspond to mumbled words, false starts, or lapsus linguae.
    """
    low_conf = []
    for seg in segments:
        for w in seg.get('words', []):
            prob = w.get('probability', 1.0)
            if prob < threshold:
                low_conf.append({
                    'word': str(w.get('word', '')).strip(),
                    'at_seconds': round(float(w.get('start', 0)), 1),
                    'confidence': prob,
                })
    return low_conf


def is_leading_silence(silence: dict) -> bool:
    """Silence before the student starts speaking — preparation/reading time."""
    if 'leading' in str(silence.get('type', '')):
        return True
    return float(silence.get('at_seconds', 1) or 1) <= 0.2


def build_audio_fluency_report(transcript: dict, all_word_scores: list, silence_report: list | None = None) -> dict:
    """Cheap recording-based fluency metrics from local ASR timings."""
    segments = transcript.get('segments', []) or []
    duration = float(transcript.get('duration_seconds') or 0)
    if not duration and segments:
        duration = max(float(seg.get('end', 0) or 0) for seg in segments)

    word_count = len([w for w in all_word_scores if str(w.get('word', '')).strip()])
    spoken_seconds = sum(
        max(0.0, float(seg.get('end', 0) or 0) - float(seg.get('start', 0) or 0))
        for seg in segments
    )
    all_silences = silence_report if silence_report is not None else detect_long_silences(segments)
    # Leading silence is preparation time (reading the source, collecting
    # thoughts before starting) — it must NOT count against fluency. Only
    # pauses DURING delivery reflect delivery quality.
    leading_silences = [s for s in all_silences if is_leading_silence(s)]
    silences = [s for s in all_silences if not is_leading_silence(s)]
    leading_seconds = sum(float(s.get('duration_seconds', 0) or 0) for s in leading_silences)
    # Remove preparation time from the effective duration so speech rate and
    # silence ratio measure the delivery itself.
    if leading_seconds and duration > leading_seconds:
        duration = duration - leading_seconds
    long_pause_seconds = sum(float(s.get('duration_seconds', 0) or 0) for s in silences)

    if duration > 0:
        speech_rate_wpm = round((word_count / duration) * 60, 1)
        silence_ratio = round(min(1.0, long_pause_seconds / duration), 3)
        spoken_ratio = round(min(1.0, spoken_seconds / duration), 3)
    else:
        speech_rate_wpm = 0
        silence_ratio = 0
        spoken_ratio = 0

    confidence_scores = [
        float(w.get('score', 0) or 0)
        for w in all_word_scores
        if w.get('score') is not None
    ]
    average_confidence = (
        round(sum(confidence_scores) / len(confidence_scores), 3)
        if confidence_scores else 0
    )
    low_confidence_words = [w for w in all_word_scores if float(w.get('score', 1) or 1) < 0.6]
    low_confidence_ratio = round(len(low_confidence_words) / word_count, 3) if word_count else 0

    rate_score = 1.0
    if speech_rate_wpm and speech_rate_wpm < 80:
        rate_score = max(0.35, speech_rate_wpm / 80)
    elif speech_rate_wpm > 180:
        rate_score = max(0.35, 1 - ((speech_rate_wpm - 180) / 120))

    pause_score = max(0.0, 1 - (silence_ratio * 2.5))
    confidence_score = average_confidence or 0.0
    fluency_score = round((rate_score * 0.35 + pause_score * 0.35 + confidence_score * 0.30) * 10, 1)

    if fluency_score >= 8:
        summary = 'Fluent delivery with manageable pauses and clear audio recognition.'
    elif fluency_score >= 6:
        summary = 'Generally understandable delivery, with some pauses or unclear words to review.'
    else:
        summary = 'Delivery needs work: pauses, pacing, or unclear pronunciation affected fluency.'

    return {
        'duration_seconds': round(duration, 1),
        'preparation_seconds': round(leading_seconds, 1),
        'word_count': word_count,
        'speech_rate_wpm': speech_rate_wpm,
        'long_pause_count': len(silences),
        'long_pause_seconds': round(long_pause_seconds, 1),
        'silence_ratio': silence_ratio,
        'spoken_ratio': spoken_ratio,
        'average_word_confidence': average_confidence,
        'low_confidence_count': len(low_confidence_words),
        'low_confidence_ratio': low_confidence_ratio,
        'fluency_score': fluency_score,
        'summary': summary,
        'method': 'local_faster_whisper_timestamps_and_confidence',
    }


def format_fluency_for_prompt(fluency: dict) -> str:
    if not fluency:
        return 'No audio fluency metrics available.'
    return (
        f"- Duration: {fluency.get('duration_seconds', 0)} seconds\n"
        f"- Speech rate: {fluency.get('speech_rate_wpm', 0)} words per minute\n"
        f"- Long pauses: {fluency.get('long_pause_count', 0)} "
        f"({fluency.get('long_pause_seconds', 0)} seconds total)\n"
        f"- Silence ratio: {int(float(fluency.get('silence_ratio', 0)) * 100)}%\n"
        f"- Average word confidence: {int(float(fluency.get('average_word_confidence', 0)) * 100)}%\n"
        f"- Low-confidence word ratio: {int(float(fluency.get('low_confidence_ratio', 0)) * 100)}%\n"
        f"- Audio fluency score: {fluency.get('fluency_score', 0)}/10\n"
        f"- Audio-based summary: {fluency.get('summary', '')}"
    )


def estimate_length_coverage(source_script: str, transcript_text: str) -> dict:
    """Cheap guardrail: very short interpretations cannot receive high coverage."""
    source_words = re.findall(r'\w+', source_script or '', flags=re.UNICODE)
    transcript_words = re.findall(r'\w+', transcript_text or '', flags=re.UNICODE)
    source_count = len(source_words)
    transcript_count = len(transcript_words)

    if source_count == 0:
        return {
            'source_word_count': 0,
            'transcript_word_count': transcript_count,
            'length_ratio': 1.0,
            'score_cap': 10.0,
        }

    ratio = min(1.0, transcript_count / source_count)

    # Interpretation is always shorter than the source — same ideas, fewer words.
    # Only cap for extremely short transcripts that cannot possibly cover the content.
    if ratio < 0.10:
        cap = 2.0
    elif ratio < 0.20:
        cap = 3.5
    elif ratio < 0.30:
        cap = 5.5
    else:
        cap = 10.0  # no cap — trust the LLM's content-based assessment

    return {
        'source_word_count': source_count,
        'transcript_word_count': transcript_count,
        'length_ratio': round(ratio, 3),
        'score_cap': cap,
    }


def reconcile_coverage_with_missing_content(result: dict) -> dict:
    """
    Enforce the coverage rubric in code: coverage_score must match the LLM's
    OWN missing_content evidence. LLMs habitually return a 'safe' 5-6 coverage
    even when their missing_content list is empty — i.e. they found nothing
    missing but scored as if a third of the speech was lost. If everything was
    covered, the score is raised to what the rubric mandates. Never lowers.
    """
    if not isinstance(result, dict):
        return result

    weights = {'high': 1.5, 'medium': 0.8, 'low': 0.4, 'minor': 0.4}
    penalty = 0.0

    missing = result.get('missing_content')
    if isinstance(missing, list):
        for item in missing:
            imp = str(item.get('importance', 'medium')).lower() if isinstance(item, dict) else 'medium'
            penalty += weights.get(imp, 0.8)

    info_loss = result.get('information_loss')
    if isinstance(info_loss, list):
        for item in info_loss:
            imp = str(item.get('importance', 'medium')).lower() if isinstance(item, dict) else 'medium'
            penalty += weights.get(imp, 0.8) * 0.6

    evidence_score = max(2.0, min(10.0, round(10.0 - penalty, 1)))

    try:
        current = float(result.get('coverage_score'))
    except (TypeError, ValueError):
        current = None

    if current is None or current < evidence_score:
        result['coverage_score'] = evidence_score
        result['coverage_reconciled_from_evidence'] = True
    return result


def apply_coverage_guardrail(result: dict, source_script: str, transcript_text: str) -> dict:
    if not isinstance(result, dict):
        return result

    coverage = estimate_length_coverage(source_script, transcript_text)
    current = result.get('coverage_score')
    try:
        current_score = float(current)
    except (TypeError, ValueError):
        current_score = None

    if current_score is not None and current_score > coverage['score_cap']:
        result['coverage_score'] = coverage['score_cap']

    result['coverage_diagnostics'] = coverage
    return result


def build_pronunciation_report(all_word_scores: list, language: str, source_script: str = '', transcript_text: str = '') -> dict:
    """
    Build an audio clarity / ASR confidence report for EN/FR using:
    1. Whisper word confidence (low confidence = likely unclear audio, not proof of mispronunciation)
    2. Reference text diffing against source translation (substitutions/omissions)
    3. Language-specific common error patterns
    """
    import difflib

    low_value_words = {
        'fr': {'le', 'la', 'les', 'de', 'des', 'du', 'un', 'une', 'et', 'a', 'à', 'en', 'au', 'aux', 'ce', 'se', 'sa', 'son'},
        'en': {'the', 'a', 'an', 'and', 'or', 'to', 'of', 'in', 'on', 'at', 'it', 'is', 'was'},
        'ar': set(),
    }

    def is_low_value_word(word: str) -> bool:
        token = normalize_repetition_word(word)
        return len(token) <= 2 or token in low_value_words.get(language, set())

    uncertain_all = [w for w in all_word_scores if w['grade'] == 'poor']
    uncertain = [w for w in uncertain_all if not is_low_value_word(w.get('word', ''))]
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
            'note': note or f'Low ASR confidence ({int(w["score"]*100)}%) — review audio clarity for this word'
        })

    return {
        'overall_score': round(overall, 3),
        'total_words': len(all_word_scores),
        'uncertain_count': len(flagged),
        'filtered_uncertain_count': max(0, len(uncertain_all) - len(flagged)),
        'warn_count': len(warn_words),
        'flagged_words': flagged,
        'summary': (
            f'Good audio clarity confidence ({int(overall*100)}%).'
            if overall >= 0.8
            else f'{len(flagged)} meaningful word(s) flagged with low ASR confidence ({int(overall*100)}% average).'
        )
    }


NUMBER_SCALE_TERMS = {
    'thousand': 'thousand',
    'thousands': 'thousand',
    'mille': 'thousand',
    'millier': 'thousand',
    'milliers': 'thousand',
    'million': 'million',
    'millions': 'million',
    'billion': 'billion',
    'billions': 'billion',
    'milliard': 'billion',
    'milliards': 'billion',
    'trillion': 'trillion',
    'trillions': 'trillion',
    'billion_fr': 'trillion',
    'billions_fr': 'trillion',
}


def normalize_number_scale_word(word: str) -> str:
    token = normalize_repetition_word(word)
    if token == 'billion':
        return 'billion'
    if token == 'billions':
        return 'billion'
    return NUMBER_SCALE_TERMS.get(token, '')


def extract_number_scale_terms(text: str) -> list[dict]:
    terms = []
    for match in re.finditer(r'\w+', text or '', flags=re.UNICODE):
        token = normalize_repetition_word(match.group(0))
        canonical = NUMBER_SCALE_TERMS.get(token)
        if canonical:
            terms.append({
                'word': match.group(0),
                'canonical': canonical,
                'position': match.start(),
            })
    return terms


def detect_number_errors(source_script: str, transcript_text: str) -> list:
    """
    Extract numbers from the source and transcript.
    Flags missing numbers and likely substitutions such as 2030 -> 2025.
    Requirement D7 from cahier des charges.
    """
    # Match integers, decimals, and grouped thousands such as 150 000 / 150,000.
    digit_chars = r'\d٠-٩'
    # Separators: space, NBSP (U+00A0), narrow NBSP (U+202F), comma,
    # Arabic thousands separator \u066c (U+066C).
    number_pattern = rf'(?<![\w])(?:[{digit_chars}]{{1,3}}(?:[ \u00a0\u202f,\u066c][{digit_chars}]{{3}})+|[{digit_chars}]+(?:[.\u066b][{digit_chars}]+)?)(?![\w])'
    source_numbers = [match.group(0) for match in re.finditer(number_pattern, source_script or '')]
    transcript_numbers = [match.group(0) for match in re.finditer(number_pattern, transcript_text or '')]

    def normalize_number(value: str) -> str:
        translation = str.maketrans('٠١٢٣٤٥٦٧٨٩٫', '0123456789.')
        normalized = str(value or '').translate(translation)
        # Strip thousands separators including Arabic \u066c (U+066C)
        normalized = re.sub(r'[\s\u00a0\u202f\u066c,](?=\d{3}(?:\D|$))', '', normalized)
        return normalized.replace(',', '.')

    def canonical_number(value: str) -> str:
        normalized = normalize_number(value)
        if re.fullmatch(r'\d+\.0+', normalized):
            normalized = normalized.split('.', 1)[0]
        if re.fullmatch(r'\d+', normalized):
            normalized = str(int(normalized))
        return normalized

    source_norm = [canonical_number(number) for number in source_numbers]
    transcript_norm = [canonical_number(number) for number in transcript_numbers]
    errors = []
    seen = set()

    def add_error(error: dict):
        key = (error.get('type'), canonical_number(error.get('expected', '')), canonical_number(error.get('heard', '')))
        if key in seen:
            return
        seen.add(key)
        errors.append(error)

    import difflib
    matcher = difflib.SequenceMatcher(a=source_norm, b=transcript_norm, autojunk=False)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            continue

        source_block = source_numbers[i1:i2]
        transcript_block = transcript_numbers[j1:j2]

        if tag == 'delete':
            for expected in source_block:
                add_error({
                    'type': 'missing',
                    'expected': expected,
                    'heard': '',
                    'message': f'{expected} was missing',
                })
            continue

        if tag == 'insert':
            # Extra numbers in the student's output are handled by the LLM
            # translation section, not counted as source-number reproduction errors.
            continue

        pair_count = min(len(source_block), len(transcript_block))
        for offset in range(pair_count):
            expected = source_block[offset]
            heard = transcript_block[offset]
            if canonical_number(expected) == canonical_number(heard):
                continue
            add_error({
                'type': 'substitution',
                'expected': expected,
                'heard': heard,
                'message': f'{expected} was rendered as {heard}',
            })

        for expected in source_block[pair_count:]:
            add_error({
                'type': 'missing',
                'expected': expected,
                'heard': '',
                'message': f'{expected} was missing',
            })

    source_scales = extract_number_scale_terms(source_script)
    transcript_scales = extract_number_scale_terms(transcript_text)
    source_scale_norm = [item['canonical'] for item in source_scales]
    transcript_scale_norm = [item['canonical'] for item in transcript_scales]
    scale_matcher = difflib.SequenceMatcher(a=source_scale_norm, b=transcript_scale_norm, autojunk=False)

    for tag, i1, i2, j1, j2 in scale_matcher.get_opcodes():
        if tag == 'equal':
            continue

        source_block = source_scales[i1:i2]
        transcript_block = transcript_scales[j1:j2]

        if tag == 'insert':
            continue

        pair_count = min(len(source_block), len(transcript_block))
        for offset in range(pair_count):
            expected = source_block[offset]['word']
            heard = transcript_block[offset]['word']
            if source_block[offset]['canonical'] == transcript_block[offset]['canonical']:
                continue
            add_error({
                'type': 'scale_substitution',
                'expected': expected,
                'heard': heard,
                'message': f'{expected} was rendered as {heard}',
            })

        for expected_item in source_block[pair_count:]:
            add_error({
                'type': 'scale_missing',
                'expected': expected_item['word'],
                'heard': '',
                'message': f'{expected_item["word"]} was missing',
            })

    return errors


def format_number_errors_for_prompt(number_errors: list) -> str:
    if not number_errors:
        return 'none found automatically'
    details = []
    for item in number_errors[:10]:
        if isinstance(item, dict):
            details.append(item.get('message') or str(item))
        else:
            details.append(str(item))
    return '; '.join(details)


def normalize_eval_text(text: str) -> str:
    import unicodedata
    normalized = unicodedata.normalize('NFKD', str(text or '').casefold())
    normalized = ''.join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r'[^\w\s]', ' ', normalized, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', normalized).strip()


def content_words(text: str) -> list[str]:
    stopwords = {
        # English
        'the', 'a', 'an', 'and', 'or', 'of', 'to', 'for', 'in', 'on', 'with', 'by',
        'this', 'that', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
        'not', 'from', 'as', 'at', 'but', 'its', 'it',
        # French
        'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'd', 'et', 'ou', 'au',
        'aux', 'pour', 'dans', 'sur', 'avec', 'par', 'ce', 'cet', 'cette', 'ces',
        'qui', 'que', 'ne', 'pas', 'est', 'sont', 'en', 'y', 'se', 'si', 'il', 'elle',
        'ils', 'elles', 'je', 'tu', 'nous', 'vous', 'on', 'me', 'te', 'lui', 'leur',
        # Arabic common function words (after normalize_eval_text removes diacritics)
        'في', 'من', 'إلى', 'على', 'أن', 'هذا', 'هذه', 'التي', 'الذي', 'ما', 'كان',
        'كانت', 'هو', 'هي', 'هم', 'لا', 'قد', 'كما', 'مع', 'أو', 'لم', 'عن', 'إن',
        'لكن', 'ذلك', 'تلك', 'هؤلاء', 'بين', 'عند', 'حتى', 'بعد', 'قبل', 'خلال',
        'ان', 'في', 'من', 'الى', 'على', 'هذا', 'هذه', 'التي', 'الذي',
    }
    return [
        word for word in normalize_eval_text(text).split()
        if len(word) > 2 and word not in stopwords
    ]


def phrase_is_present(claimed_phrase: str, transcript_text: str) -> bool:
    phrase = normalize_eval_text(claimed_phrase)
    transcript = normalize_eval_text(transcript_text)
    if not phrase or not transcript:
        return False
    if phrase in transcript:
        return True

    words = content_words(claimed_phrase)
    if len(words) < 2:
        return False
    present = sum(1 for word in words if re.search(rf'\b{re.escape(word)}\b', transcript))
    return present >= max(2, int(len(words) * 0.75))


def remove_false_missing_translation_errors(result: dict, transcript_text: str) -> dict:
    if not isinstance(result, dict):
        return result

    filtered = []
    for item in result.get('translation_errors', []) or []:
        if not isinstance(item, dict):
            filtered.append(item)
            continue

        explanation = normalize_eval_text(item.get('explanation', ''))
        if not any(term in explanation for term in ['missing', 'omitted', 'omit', 'absence', 'manquant']):
            filtered.append(item)
            continue

        claimed_parts = [
            item.get('student_said', ''),
            item.get('correct_translation', ''),
        ]
        if any(phrase_is_present(part, transcript_text) for part in claimed_parts):
            continue

        # Also inspect quoted phrases in the explanation, e.g. "missing 'pour les communautés...'".
        quoted = re.findall(r"['\"]([^'\"]{4,})['\"]", str(item.get('explanation', '')))
        if any(phrase_is_present(part, transcript_text) for part in quoted):
            continue

        filtered.append(item)

    result['translation_errors'] = filtered
    return result


def clean_translation_error_items(result: dict) -> dict:
    """Keep only actionable mistranslations in translation_errors."""
    if not isinstance(result, dict):
        return result

    cleaned = []
    missing = result.setdefault('missing_content', [])
    if not isinstance(missing, list):
        missing = []
        result['missing_content'] = missing

    non_actionable_terms = [
        # English
        'nothing needs to be fixed', 'nothing to fix', 'no correction needed',
        'no correction is needed', 'correct translation', 'translation is correct',
        'accurate translation', 'not wrong', 'no error', 'well translated',
        'correctly translated', 'faithful translation', 'good translation',
        # French
        'pas d erreur', 'pas de correction', 'aucune correction', 'traduction correcte',
        'bien traduit', 'bien rendu', 'fidele', 'traduction fidele', 'traduction fidèle',
        'aucune erreur', 'pas d erreurs', 'rendu correct', 'traduction accurate',
        # Arabic
        'لا يوجد خطأ', 'لا توجد أخطاء', 'لا توجد اخطاء', 'ترجمة صحيحة',
        'ترجمة دقيقة', 'ترجمة سليمة', 'لا حاجة للتصحيح', 'مترجم بشكل صحيح',
        'لا خطأ', 'صحيح', 'ترجمة أمينة',
    ]
    omission_terms = [
        'completely omitted', 'omitted', 'missing', 'not mentioned',
        'student said nothing', 'absence', 'manquant', 'omis', 'absent',
        'غائب', 'محذوف', 'لم يذكر',
    ]
    wrong_terms = [
        'wrong', 'incorrect', 'mistranslat', 'substitution',
        'wrong number', 'number error', 'nombre incorrect', 'faux nombre',
        'contresens', 'faux sens', 'خطأ', 'غلط', 'مغلوط',
    ]

    for item in result.get('translation_errors', []) or []:
        if not isinstance(item, dict):
            cleaned.append(item)
            continue

        student_said = normalize_eval_text(item.get('student_said', ''))
        explanation = normalize_eval_text(item.get('explanation', ''))
        combined = normalize_eval_text(' '.join(str(item.get(key, '')) for key in ['student_said', 'correct_translation', 'explanation']))

        if any(term in combined for term in non_actionable_terms):
            continue

        is_empty_student = not student_said or student_said in {'none', 'nothing', 'n/a', 'na', 'null'}
        has_actionable_error = any(term in explanation for term in wrong_terms)
        is_omission = (is_empty_student or any(term in explanation for term in omission_terms)) and not has_actionable_error
        if is_omission:
            content = item.get('source_text') or item.get('correct_translation') or item.get('explanation')
            if content:
                missing.append({'content': content, 'importance': 'high'})
            continue

        cleaned.append(item)

    result['translation_errors'] = cleaned
    return result


_NUMBER_IN_TEXT_RE = re.compile(r'\b\d+(?:[.,]\d+)?%?\b')
_NUMBER_EXPLANATION_TERMS = {
    'percentage', 'pourcentage', 'percent', 'number error', 'wrong number',
    'incorrect percentage', 'nombre incorrect', 'faux pourcentage', 'chiffre incorrect',
    'statistique', 'statistic', 'wrong figure', 'faux chiffre', 'nombre erron',
    'wrong statistic', 'nombre faux', 'chiffre faux', 'chiffre erron',
    'wrong percentage', 'incorrect number', 'incorrect figure',
}


def filter_number_only_translation_errors(result: dict) -> dict:
    """
    Remove items from translation_errors where the sole discrepancy is a
    number/percentage/statistic difference — those are already in number_accuracy.
    """
    if not isinstance(result, dict):
        return result

    cleaned = []
    for item in result.get('translation_errors', []) or []:
        if not isinstance(item, dict):
            cleaned.append(item)
            continue

        explanation = normalize_eval_text(item.get('explanation', ''))
        is_number_error = any(term in explanation for term in _NUMBER_EXPLANATION_TERMS)

        if not is_number_error:
            source_text = str(item.get('source_text', '') or '')
            student_said = str(item.get('student_said', '') or '')
            if source_text and student_said:
                src_nums = _NUMBER_IN_TEXT_RE.findall(source_text)
                std_nums = _NUMBER_IN_TEXT_RE.findall(student_said)
                if src_nums and std_nums and src_nums != std_nums:
                    src_stripped = normalize_eval_text(_NUMBER_IN_TEXT_RE.sub('NUM', source_text))
                    std_stripped = normalize_eval_text(_NUMBER_IN_TEXT_RE.sub('NUM', student_said))
                    if src_stripped == std_stripped:
                        is_number_error = True

        if not is_number_error:
            cleaned.append(item)

    result['translation_errors'] = cleaned
    return result


def is_french_silent_plural_s_error(item: dict) -> bool:
    """French final plural -s is silent; ASR spelling alone cannot prove omission."""
    text = ' '.join(
        str(item.get(key, ''))
        for key in ['text', 'word', 'source_text', 'student_said', 'correct_translation', 'explanation', 'correction', 'likely_issue']
    ).casefold()
    if not text:
        return False
    mentions_plural_s = (
        'plural' in text
        or 'pluriel' in text
        or 'final s' in text
        or 's final' in text
        or 'omitted the s' in text
        or 'missing s' in text
        or 'omit s' in text
        or 'omission du s' in text
        or 's manquant' in text
    )
    mentions_omission = any(term in text for term in ['omit', 'omission', 'missing', 'manquant', 'oubli'])
    return mentions_plural_s and mentions_omission


def filter_french_silent_plural_errors(result: dict, language: str) -> dict:
    if language != 'fr' or not isinstance(result, dict):
        return result

    for key in ['language_errors', 'pronunciation_flags', 'translation_errors', 'terminology_problems']:
        values = result.get(key)
        if isinstance(values, list):
            result[key] = [
                item for item in values
                if not (isinstance(item, dict) and is_french_silent_plural_s_error(item))
            ]

    pronunciation = result.get('pronunciation')
    if isinstance(pronunciation, dict) and isinstance(pronunciation.get('diff_errors'), list):
        pronunciation['diff_errors'] = [
            item for item in pronunciation['diff_errors']
            if not (isinstance(item, dict) and is_french_silent_plural_s_error(item))
        ]

    return result


_SHORT_PARTICLES = {
    'en': {'a', 'an', 'the', 'i', 'to', 'of', 'in', 'is', 'it', 'as', 'at', 'by', 'or', 'if', 'up', 'do', 'so',
           'we', 'he', 'my', 'on', 'be', 'am', 'are', 'was', 'were', 'has', 'had', 'have', 'not', 'no',
           'its', 'our', 'you', 'she', 'they', 'this', 'that', 'with', 'from', 'for', 'and', 'but'},
    'fr': {'a', 'à', 'au', 'aux', 'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une',
           'je', 'il', 'elle', 'on', 'nous', 'vous', 'ils', 'elles', 'tu',
           'ou', 'et', 'en', 'y', 'ce', 'se', 'sa', 'son', 'ses', 'leur', 'leurs',
           'que', 'qui', 'ne', 'pas', 'plus', 'si', 'car', 'par', 'sur', 'dans',
           'est', 'sont', 'était', 'ont', 'eu', 'été', 'me', 'te', 'lui',
           'cet', 'cette', 'ces', 'mon', 'ton', 'ma', 'ta', 'mes', 'tes',
           'mais', 'donc', 'or', 'ni', 'car', 'puis', 'avec'},
    'ar': {'في', 'من', 'إلى', 'على', 'أن', 'هذا', 'هذه', 'التي', 'الذي', 'ما', 'كان', 'كانت',
           'هو', 'هي', 'هم', 'لا', 'قد', 'كما', 'مع', 'أو', 'لم', 'عن', 'إن', 'لكن'},
}


def detect_repetitions_timing_window(segments: list, language: str = 'ar',
                                      max_gap_seconds: float = 1.5) -> list:
    """
    Detect word repetitions using timing: if the same word appears twice within
    max_gap_seconds in the word timestamp list, it's a repetition — even when
    the ASR segment text has already been deduplicated (Groq and faster-whisper
    both normalize consecutive repeated words in the text output).

    _SHORT_PARTICLES are skipped to avoid flagging frequent function words
    ("the the", "le le") that ASR sometimes duplicates in timestamps even when
    the student said them only once.
    """
    skip_words = _SHORT_PARTICLES.get(language, set())
    words = get_word_timing_sequence(segments)
    repetitions = []
    seen_keys = set()
    consumed_as_second = set()  # indices already matched as second occurrence

    for i, w in enumerate(words):
        if i in consumed_as_second:
            continue
        word = normalize_repetition_word(w['word'])
        if len(word) < 2 or word in skip_words:
            continue
        for j in range(i + 1, len(words)):
            nw = words[j]
            gap = nw['start'] - w['end']
            if gap > max_gap_seconds:
                break
            next_word = normalize_repetition_word(nw['word'])
            if words_are_repetition_equivalent(word, next_word, language):
                key = (word, round(w['start'], 1))
                if key not in seen_keys:
                    seen_keys.add(key)
                    consumed_as_second.add(j)
                    repetitions.append({
                        'word': w['word'],
                        'at_seconds': round(w['start'], 1),
                        'second_occurrence': round(nw['start'], 1),
                        'gap_words': j - i,
                        'source': 'timing_window',
                    })
                break

    return repetitions


def detect_cut_words(segments: list, language: str = 'ar') -> list:
    """
    Detect cut/restarted words from word-level timestamps: a very short word
    (< 0.18 s) immediately followed (gap < 0.6 s) by a word starting with the
    same first 2+ characters — the student cut the word mid-way and restarted
    it ("clim- climate"). These count as hesitations per the cahier des
    charges (D5 disfluency category).

    The old ultra-short-blip branch (<0.10 s regardless of next word) was
    removed: it flagged ASR timing noise, not real disfluencies.
    """
    words = get_word_timing_sequence(segments)
    particles = _SHORT_PARTICLES.get(language, set())
    cut_words = []

    for i, w in enumerate(words[:-1]):
        word = normalize_repetition_word(w['word'])
        if not word or word in particles:
            continue
        duration = w['end'] - w['start']
        if duration >= 0.18:
            continue
        nw = words[i + 1]
        gap = nw['start'] - w['end']
        if gap > 0.6:
            continue
        next_word = normalize_repetition_word(nw['word'])
        # Short word is a prefix of the next (longer) word → cut + restart.
        # next word must be strictly longer, otherwise "de de" (a repetition,
        # not a cut word) would be double-counted here.
        prefix_len = min(len(word), 3)
        if len(word) >= 2 and len(next_word) > len(word) and next_word.startswith(word[:prefix_len]):
            cut_words.append({
                'word': w['word'],
                'at_seconds': round(w['start'], 1),
                'confidence': 1.0,
                'source': 'cut_word',
            })

    return cut_words


def run_full_analysis(source_script: str, transcript: dict, language: str = 'ar') -> dict:
    """
    Run all error detection — combines word-level (when available) and text-based detection.
    Text-based detection works even when Groq transcript has no word timestamps.
    """
    segments  = transcript.get('segments', [])
    full_text = transcript.get('full_text', '')

    # Word-level detection (works when faster-whisper is used)
    silences        = detect_long_silences(segments)
    word_reps       = detect_repetitions(segments, language)
    word_hesitations = detect_hesitation_words(segments, language)
    low_conf        = detect_low_confidence_words(segments)
    number_errs     = detect_number_errors(source_script, full_text)

    # Timing-window repetition: catches words the ASR deduplicated in text but
    # kept as separate entries in the word-timestamp list (Groq and faster-whisper).
    timing_reps = detect_repetitions_timing_window(segments, language)

    # Cut/restarted words ("clim- climate") count as hesitations (D5 in
    # cahier des charges) — a filler and a cut word are the same disfluency.
    cut_words = detect_cut_words(segments, language)

    # Text-based detection (always works, even with Groq transcript)
    text_hesitations = detect_hesitations_from_text(full_text, language)
    text_repetitions = detect_repetitions_from_text(full_text, language)

    # Merge: timing-window reps win over word-level (more reliable for Groq),
    # text reps fill remaining gaps.
    all_hesitations = merge_hesitation_reports(word_hesitations, text_hesitations)
    for cw in cut_words:
        if not any(abs(float(h.get('at_seconds') or -99) - cw['at_seconds']) < 0.3
                   for h in all_hesitations):
            all_hesitations.append(cw)
    all_repetitions = merge_repetition_reports(timing_reps, word_reps, text_repetitions)

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
    glossary_block  = build_glossary_block(json.dumps(data.get('glossary'))
                                           if isinstance(data.get('glossary'), list)
                                           else str(data.get('glossary', '') or ''))

    if not transcript_text:
        return jsonify({'error': 'transcript_text is required'}), 400

    # Strip ASR hallucination artifacts (elongated garbage tokens) before analysis
    transcript_text, asr_artifacts = remove_asr_artifacts(transcript_text)

    # Run algorithmic analysis on segments
    algo = run_full_analysis(source_script, transcript_obj, language) if transcript_obj else {
        'long_silences': [], 'repetitions': [], 'hesitation_words': [],
        'number_errors': [], 'summary': {}
    }
    s = algo.get('summary', {})

    try:
        from utils.groq_client import get_groq_client
        client = get_groq_client()

        rep_examples  = ', '.join(f'"{r["word"]}"' for r in (algo.get('repetitions', [])[:3]))
        hes_examples  = ', '.join(f'"{h["word"]}"' for h in (algo.get('hesitation_words', [])[:3]))
        sil_examples  = format_silences_for_prompt(algo.get('long_silences', []))
        coverage_diagnostics = estimate_length_coverage(source_script, transcript_text)

        lang_names = {'ar': 'Arabic', 'fr': 'French', 'en': 'English', 'unknown': 'an unknown language'}
        _raw_src = data.get('source_language', '')
        _src_key = _raw_src if _raw_src and _raw_src != language else 'unknown'
        prompt = _safe_format(
            LLM_ANALYSIS_PROMPT,
            source_language=lang_names.get(_src_key, _src_key),
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
            number_error_details=format_number_errors_for_prompt(algo.get('number_errors', [])),
            coverage_diagnostics=coverage_diagnostics,
            fluency_summary=format_fluency_for_prompt({}),
            uncertain_words='(not available in text-only mode)',
            glossary_block=glossary_block,
            proper_nouns_block=build_proper_nouns_block(source_script),
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
            max_tokens=6000,
            temperature=0.2
        )

        llm_result = _extract_json(response.choices[0].message.content)
        llm_result = strip_foreign_script_chars(llm_result)
        llm_result = remove_false_missing_translation_errors(llm_result, transcript_text)
        llm_result = clean_translation_error_items(llm_result)
        llm_result = filter_number_only_translation_errors(llm_result)
        llm_result = reclassify_garbage_translation_errors(llm_result)
        llm_result = filter_equivalent_number_renderings(llm_result)
        llm_result = reconcile_coverage_with_missing_content(llm_result)
        llm_result = apply_coverage_guardrail(llm_result, source_script, transcript_text)
        if asr_artifacts:
            llm_result['unclear_audio_tokens'] = asr_artifacts
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
        return jsonify({'error': str(e), 'algorithmic': algo}), 500


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
    glossary_block   = build_glossary_block(request.form.get('glossary', ''))
    _raw_src_lang    = request.form.get('source_language', '')
    # Avoid telling the LLM source==target (monolingual confusion) when not explicitly set
    source_language  = _raw_src_lang if _raw_src_lang and _raw_src_lang != language else 'unknown'

    from modules.module_c import _safe_audio_ext
    ext       = _safe_audio_ext(audio_file.filename)
    temp_path = os.path.join(UPLOAD_FOLDER, f'eval_{uuid.uuid4().hex[:8]}{ext}')
    audio_file.save(temp_path)

    try:
        from modules.module_c import DISFLUENCY_PROMPTS
        disfluency_prompt = DISFLUENCY_PROMPTS.get(language, DISFLUENCY_PROMPTS['en'])
        # Style-priming only — Whisper imitates the prompt's disfluent style;
        # appending instruction text does nothing and wastes the prompt budget.
        verbatim_prompt = disfluency_prompt

        # ASR strategy: Groq whisper-large-v3 with WORD timestamps first —
        # far better recognition (especially Arabic) and seconds instead of
        # minutes. Local faster-whisper (medium) is the fallback; it also
        # provides per-word confidence, which the cloud API does not.
        asr_method = 'local_faster_whisper_medium'
        groq_asr = transcribe_eval_with_groq(temp_path, language, verbatim_prompt)

        if groq_asr is not None:
            asr_method = 'groq_whisper_large_v3'
            all_segments = groq_asr['segments']
            all_word_scores = groq_asr['word_scores']
            segment_text = groq_asr['segment_text']
            detected_language = groq_asr['language']
            language_confidence = 1.0
            duration_value = groq_asr['duration']
        else:
            from modules.module_c import _get_local_model
            model = _get_local_model()
            repetition_hotwords = build_repetition_hotwords(source_script, language)

            segments_iter, info = model.transcribe(
                temp_path,
                language=language,
                task='transcribe',
                word_timestamps=True,
                vad_filter=False,               # disabled: preserves silence gaps between segments
                suppress_tokens=[],             # preserve fillers/repetitions, no normalization
                suppress_blank=False,
                condition_on_previous_text=False,
                compression_ratio_threshold=100.0,  # disable repetition fallback — keeps repeated words
                log_prob_threshold=-100.0,          # disable low-prob fallback — keeps hesitations
                no_speech_threshold=0.95,
                temperature=0.0,                    # greedy decoding — no randomness
                beam_size=1,                        # greedy: prevents beam search from collapsing repetitions
                repetition_penalty=1.0,
                no_repeat_ngram_size=0,
                initial_prompt=verbatim_prompt,      # language-specific filler + repetition priming
                hotwords=repetition_hotwords,
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

            segment_text = full_text.strip()
            detected_language = info.language
            language_confidence = round(info.language_probability, 3)
            duration_value = round(info.duration, 1)

        word_timestamp_text = build_transcript_from_word_timestamps(all_segments)
        full_text = word_timestamp_text or segment_text
        # Strip ASR hallucination artifacts (e.g. one character stretched dozens
        # of times over unclear audio) so they are never treated as student speech.
        full_text, asr_artifacts = remove_asr_artifacts(full_text)
        # Strip all ellipsis Groq/Whisper inserts for silent/unclear audio.
        full_text = re.sub(r'\.{2,}', '', full_text).strip()
        full_text = re.sub(r'…', '', full_text).strip()
        full_text = re.sub(r'\s{2,}', ' ', full_text).strip()
        transcript = {
            'full_text':           full_text,
            'segment_text':        segment_text,
            'word_timestamp_text': word_timestamp_text,
            'segments':            all_segments,
            'language_detected':   detected_language,
            'language_confidence': language_confidence,
            'duration_seconds':    duration_value,
        }

        # Step 2: Full algorithmic analysis (now WITH word timestamps)
        algo = run_full_analysis(source_script, transcript, language)
        audio_silences = detect_audio_silences(temp_path)
        if audio_silences:
            algo['long_silences'] = merge_silence_reports(algo.get('long_silences', []), audio_silences)
            algo['audio_silences'] = audio_silences
            algo.setdefault('summary', {})['silence_count'] = len(algo['long_silences'])
        # Hesitations from audio (what the ASR silently cleaned out):
        # - voiced short gaps = filled pauses ("euhhh") the recognizer skipped
        # - short burst→silence→speech = a word cut mid-way and restarted
        # Both are genuine hesitations (D5).
        audio_filled  = detect_audio_filled_pauses(temp_path, transcript.get('segments', []))
        audio_cut     = detect_cut_words_from_audio(temp_path)
        # A voiced burst inside a word gap can trigger both detectors for the
        # same event — keep the filled-pause reading, drop the duplicate.
        audio_cut = [c for c in (audio_cut or [])
                     if not any(abs(c['at_seconds'] - f.get('at_seconds', -99)) < 0.6
                                for f in (audio_filled or []))]
        all_audio_hes = (audio_filled or []) + audio_cut
        if all_audio_hes:
            algo['audio_hesitations'] = all_audio_hes
            algo['hesitation_words'] = merge_hesitation_reports(
                algo.get('hesitation_words', []),
                all_audio_hes,
            )
            algo.setdefault('summary', {})['hesitation_count'] = len(algo['hesitation_words'])
        s    = algo.get('summary', {})
        fluency = build_audio_fluency_report(transcript, all_word_scores, algo.get('long_silences', []))

        # Step 3: LLM analysis with accurate data
        from utils.groq_client import get_groq_client
        client = get_groq_client()

        lang_names = {'ar': 'Arabic', 'fr': 'French', 'en': 'English', 'unknown': 'an unknown language'}
        rep_examples     = ', '.join(f'"{r.get("word","")}"' for r in algo.get('repetitions', [])[:3])
        hes_examples     = ', '.join(f'"{h.get("word","")}"' for h in algo.get('hesitation_words', [])[:3])
        sil_examples     = format_silences_for_prompt(algo.get('long_silences', []))
        uncertain_words  = [w for w in all_word_scores if w['grade'] == 'poor']
        if asr_method.startswith('groq'):
            uncertain_str = ('(per-word confidence is not provided by the cloud recognizer — '
                             'judge pronunciation only from the audio metrics and clear evidence in the transcript)')
        else:
            uncertain_str = ', '.join(
                f'"{w["word"]}" (confidence {w["score"]})'
                for w in uncertain_words[:10]
            ) or 'none flagged'
        coverage_diagnostics = estimate_length_coverage(source_script, full_text)

        prompt = _safe_format(
            LLM_ANALYSIS_PROMPT,
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
            number_error_details=format_number_errors_for_prompt(algo.get('number_errors', [])),
            coverage_diagnostics=coverage_diagnostics,
            fluency_summary=format_fluency_for_prompt(fluency),
            uncertain_words=uncertain_str,
            glossary_block=glossary_block,
            proper_nouns_block=build_proper_nouns_block(source_script),
        )

        # Base result returned even if LLM step fails below
        _algo_payload = {
            'long_silences':    algo.get('long_silences', []),
            'repetitions':      algo.get('repetitions', []),
            'hesitation_words': algo.get('hesitation_words', []),
            'number_errors':    algo.get('number_errors', []),
            'summary':          s,
        }

        try:
            response = client.chat.completions.create(
                model=PRIMARY_LLM_MODEL,
                messages=[
                    {'role': 'system', 'content':
                     'You are an expert interpreter training evaluator at ETIB Beirut. '
                     'Return only valid JSON. Be thorough — detect ALL error types listed.'},
                    {'role': 'user', 'content': prompt}
                ],
                max_tokens=6000,
                temperature=0.2
            )
            llm_result = _extract_json(response.choices[0].message.content)
        except Exception as llm_err:
            import traceback; traceback.print_exc()
            return jsonify({
                'error': f'LLM evaluation unavailable: {llm_err}',
                'llm_failed': True,
                'algorithmic': _algo_payload,
                'fluency':     fluency,
                'asr_method':  asr_method,
                'transcript':  transcript,
            }), 207

        llm_result = strip_foreign_script_chars(llm_result)
        llm_result = remove_false_missing_translation_errors(llm_result, full_text)
        llm_result = clean_translation_error_items(llm_result)
        llm_result = filter_number_only_translation_errors(llm_result)
        llm_result = reclassify_garbage_translation_errors(llm_result)
        llm_result = filter_equivalent_number_renderings(llm_result)
        llm_result = reconcile_coverage_with_missing_content(llm_result)
        llm_result = apply_coverage_guardrail(llm_result, source_script, full_text)
        if asr_artifacts:
            llm_result['unclear_audio_tokens'] = asr_artifacts
        llm_result['algorithmic'] = _algo_payload
        llm_result['fluency'] = fluency
        llm_result['asr_method'] = asr_method

        # Step 4: Pronunciation report (whisper confidence + language-specific patterns)
        pronun_report = build_pronunciation_report(all_word_scores, language=language)
        llm_result['pronunciation'] = pronun_report
        llm_result['transcript'] = transcript

        # Step 5: Persist session for history / adaptive difficulty (D11-D12).
        # Guests have no account: their sessions are NOT saved, otherwise all
        # guests would share one "anonymous" history and see each other's data.
        user_id = _current_user_id()
        if user_id != 'anonymous':
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

    try:
        from utils.groq_client import get_groq_client
        client = get_groq_client()

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
            max_tokens=3500,
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
    """Return the last N evaluation sessions for the current user (D11)."""
    user_id = _current_user_id()
    if user_id == 'anonymous':
        # Guests have no account — no history (and no shared anonymous pool).
        return jsonify({'sessions': [], 'count': 0, 'guest': True})
    try:
        limit = min(int(request.args.get('limit', 20)), 50)
    except (ValueError, TypeError):
        limit = 20
    sessions = _load_sessions(user_id, limit=limit)
    return jsonify({'sessions': sessions, 'count': len(sessions)})


@module_d_bp.route('/adaptive-params', methods=['GET'])
def adaptive_params():
    """Analyse recent sessions and return recommended Module A parameters + trend + problems (D12)."""
    user_id = _current_user_id()
    if user_id == 'anonymous':
        return jsonify(_compute_adaptive_params([]))
    sessions = _load_sessions(user_id, limit=20)
    return jsonify(_compute_adaptive_params(sessions))


@module_d_bp.route('/history/<session_id>')
def get_history(session_id: str):
    """Return a single session by id (D11)."""
    user_id = _current_user_id()
    if not user_id or user_id == 'anonymous':
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
