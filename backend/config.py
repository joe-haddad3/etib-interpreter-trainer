"""
ETIB Platform — Central Configuration
======================================
All constants and config values live here.
Import from this file instead of hardcoding values in modules.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ─────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GOOGLE_AI_KEY = os.getenv('GOOGLE_AI_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # paid fallback only

# ── Arabic evaluation micro-service (Ali's FastAPI wrapper) ─────────────────
# Independent Arabic i'rab/tanween/pronunciation service. We only talk to it
# over HTTP, so this Flask app never imports FastAPI code or loads the heavy
# wav2vec2 models. Empty URL = feature off (existing evaluation unchanged).
ARABIC_WRAPPER_URL = os.getenv('ARABIC_WRAPPER_URL', '').strip()
ARABIC_WRAPPER_API_KEY = os.getenv('ARABIC_WRAPPER_API_KEY', '').strip()
ARABIC_WRAPPER_TIMEOUT = int(os.getenv('ARABIC_WRAPPER_TIMEOUT', '180'))

LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'groq')  # groq | local_aya | remote_aya
PRIMARY_LLM_MODEL = 'openai/gpt-oss-120b'        # via Groq (free) — llama-3.3-70b
                                                 # was retired by Groq (17 Aug 2026).
FALLBACK_LLM_MODEL = 'gemini-1.5-flash'          # via Google AI Studio (free)


def groq_extra_params(model: str) -> dict:
    """gpt-oss / qwen on Groq are REASONING models — they emit chain-of-thought
    that breaks our strict-JSON parsing (and can eat the token budget). Hide the
    reasoning and keep it short so only the JSON answer comes back. Passed via
    extra_body since the installed groq SDK doesn't accept these as kwargs."""
    if 'gpt-oss' in model or 'qwen' in model:
        return {'extra_body': {'reasoning_effort': 'low', 'reasoning_format': 'hidden'}}
    return {}
LOCAL_MODEL_ID = os.getenv('LOCAL_MODEL_ID', 'CohereLabs/aya-expanse-8b')
LOCAL_MODEL_PATH = os.getenv('LOCAL_MODEL_PATH', '').strip()
LOCAL_MODEL_DEVICE_MAP = os.getenv('LOCAL_MODEL_DEVICE_MAP', 'auto')
LOCAL_MODEL_TORCH_DTYPE = os.getenv('LOCAL_MODEL_TORCH_DTYPE', 'auto')
REMOTE_AYA_URL = os.getenv('REMOTE_AYA_URL', '').strip()
REMOTE_AYA_TIMEOUT_SECONDS = int(os.getenv('REMOTE_AYA_TIMEOUT_SECONDS', '300'))
REMOTE_AYA_VERIFY_SSL = os.getenv('REMOTE_AYA_VERIFY_SSL', 'true').strip().lower() not in {
    '0',
    'false',
    'no',
    'off',
}

# ── TTS ─────────────────────────────────────────────────────────────────────
# edge-tts voice names — chosen after Day 1 evaluation
# Person 4 will update these after listening to samples
TTS_VOICES = {
    'ar': {
        'LB': 'ar-LB-RamiNeural',       # Lebanese — closest to ETIB students
        'LB_f': 'ar-LB-LaylaNeural',    # Lebanese female
        'SA': 'ar-SA-ZariyahNeural',    # Gulf female
        'SA_m': 'ar-SA-HamedNeural',    # Gulf male (professor feedback: voice diversity)
        'EG': 'ar-EG-SalmaNeural',      # Egyptian female
        'EG_m': 'ar-EG-ShakirNeural',   # Egyptian male
        'MA': 'ar-MA-MounaNeural',      # Maghreb (Morocco) female
        'MA_m': 'ar-MA-JamalNeural',    # Maghreb (Morocco) male
    },
    'fr': {
        'FR': 'fr-FR-DeniseNeural',
        'FR_m': 'fr-FR-HenriNeural',
        'CA': 'fr-CA-SylvieNeural',
        'CA_m': 'fr-CA-AntoineNeural',  # Québécois male
    },
    'en': {
        'US': 'en-US-JennyNeural',
        'US_m': 'en-US-GuyNeural',      # US male — for two-voice dialogues
        'GB': 'en-GB-SoniaNeural',
        'GB_m': 'en-GB-RyanNeural',
        'AU': 'en-AU-NatashaNeural',
        'IE': 'en-IE-EmilyNeural',      # Irish
        'IE_m': 'en-IE-ConnorNeural',
        # Non-native-accented English speaker, common in international
        # institutions — students should be able to train on this too.
        'IN': 'en-IN-NeerjaNeural',
        'IN_m': 'en-IN-PrabhatNeural',
    }
}

DEFAULT_VOICE = {
    'ar': TTS_VOICES['ar']['LB'],
    'fr': TTS_VOICES['fr']['FR'],
    'en': TTS_VOICES['en']['US'],
}

# ── ASR ─────────────────────────────────────────────────────────────────────
WHISPER_MODEL_SIZE = 'medium'     # good Arabic quality, practical on CPU (~500MB)
WHISPER_DEVICE = 'cpu'            # change to 'cuda' if GPU available
WHISPER_COMPUTE_TYPE = 'int8'     # int8 = faster on CPU

# Silence threshold for Module D error detection
SILENCE_THRESHOLD_MS = 500        # gaps > 500ms flagged as possible omission

# ── File paths ───────────────────────────────────────────────────────────────
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
AUDIO_OUTPUT_FOLDER = os.getenv('AUDIO_OUTPUT_FOLDER', './audio_outputs')

# ── MongoDB ─────────────────────────────────────────────────────────────────
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017')
MONGODB_DB  = os.getenv('MONGODB_DB',  'etib_interpreter_trainer')

# ── Speech generation defaults ───────────────────────────────────────────────
DEFAULT_WORD_COUNT = 250
DEFAULT_WPM = 120           # words per minute delivery rate
DEFAULT_LANGUAGE = 'ar'     # Arabic is the primary language per cahier des charges
DEFAULT_DIFFICULTY = 'intermediate'

# ── Evaluation scope ─────────────────────────────────────────────────────────
# Professor bilan (23 July 2026): "Se contenter à ce stade de nous concentrer
# sur la conformité à la terminologie, la gestion du décalage, des pauses, la
# correction linguistique — ET NON celle de la restitution du sens du discours."
# The automatic meaning/sense judgement was unreliable (false errors, inexact
# corrections), so it must NOT drive the score. When False, the evaluation
# grades ONLY terminology conformity, linguistic correctness, pronunciation, and
# delivery (pauses / décalage / fluency); meaning & coverage stay in the report
# as informational feedback but never lower overall_score. Set the env var
# EVALUATION_SCORE_ON_MEANING=true to restore full meaning-based scoring.
EVALUATION_SCORE_ON_MEANING = os.getenv('EVALUATION_SCORE_ON_MEANING', 'false').lower() == 'true'

# ETIB feedback (Lina, 21 Aug 2026): "Pour l'evaluation, il faudrait supprimer
# tout ce qui est en rapport avec le sens et le contenu. Les etudiants doivent
# savoir exactement ce qui peut etre evalue par IA (terminologie, nombres/dates,
# silences, hesitations, eventuellement les fautes de langue)."
# EVALUATION_SCORE_ON_MEANING above already keeps meaning OUT OF THE SCORE.
# This second flag keeps it out of the REPORT entirely: when False, the
# meaning/content blocks (translation_errors, missing_content, coverage_score)
# are dropped from the response and the LLM is told not to produce them, so a
# student never sees an automatic meaning judgement. Set the env var
# EVALUATION_REPORT_MEANING=true to show them again as informational feedback
# (that is what Kevin asked for on 12 Aug 2026 — the two requests conflict, so
# the behaviour is a single switch instead of a hard-coded choice).
EVALUATION_REPORT_MEANING = os.getenv('EVALUATION_REPORT_MEANING', 'false').lower() == 'true'

# ── Terminology grounding (ETIB feedback, Lina — 21 Aug 2026) ───────────────
# The generated glossary is checked against the institutional bases that expose a
# public API (see services/terminology.py): UNBIS Thesaurus for UN terminology
# in AR/FR/EN, IATE for EU terminology in FR/EN, FranceTerme for officially
# recommended French terms. Entirely fail-open — set the flag to false to skip
# the lookups altogether.
TERMINOLOGY_GROUNDING_ENABLED = os.getenv('TERMINOLOGY_GROUNDING_ENABLED', 'true').lower() != 'false'
TERMINOLOGY_TIMEOUT = int(os.getenv('TERMINOLOGY_TIMEOUT', '6'))      # seconds per HTTP call
TERMINOLOGY_MAX_TERMS = int(os.getenv('TERMINOLOGY_MAX_TERMS', '20')) # terms grounded per glossary
# FranceTerme is a ~9 MB open-data XML export, downloaded lazily on first use and
# then held in memory. Set to false on a very memory-tight deployment.
FRANCETERME_ENABLED = os.getenv('FRANCETERME_ENABLED', 'true').lower() != 'false'

# Domain lock (user request, 25 Aug 2026). The selected domain is stated as a hard
# constraint in the generation prompt, and the finished speech is checked once; a
# speech that drifted is revised back inside its domain. The check costs one small
# LLM call per generation (the revision only runs when the speech actually
# drifted), so it can be switched off if quota is tight.
DOMAIN_ENFORCEMENT_ENABLED = os.getenv('DOMAIN_ENFORCEMENT_ENABLED', 'true').lower() != 'false'
