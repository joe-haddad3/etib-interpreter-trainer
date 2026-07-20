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

LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'groq')  # groq | local_aya | remote_aya
PRIMARY_LLM_MODEL = 'llama-3.3-70b-versatile'   # via Groq (free)
FALLBACK_LLM_MODEL = 'gemini-1.5-flash'          # via Google AI Studio (free)
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
