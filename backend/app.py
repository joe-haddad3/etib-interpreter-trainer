"""
ETIB Interpreter Self-Training Platform — Flask Backend
=======================================================
Entry point. Registers all module blueprints and starts the server.

Run with:
    cd backend
    python app.py
"""
import os
from flask import Flask, jsonify, request, g
from dotenv import load_dotenv

load_dotenv(override=True)

from config import LLM_PROVIDER, LOCAL_MODEL_ID, REMOTE_AYA_URL

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-in-prod')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB — audio files can be large

_ALLOWED_ORIGINS = {
    'https://etib-interpreter-trainer.vercel.app',
    'http://127.0.0.1:5174',
    'http://localhost:5174',
    'http://127.0.0.1:5173',
    'http://localhost:5173',
}
for _o in os.getenv('ALLOWED_ORIGINS', '').split(','):
    _o = _o.strip()
    if _o:
        _ALLOWED_ORIGINS.add(_o)

@app.after_request
def add_cors(response):
    origin = request.headers.get('Origin', '')
    if origin in _ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Groq-Api-Key'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Vary'] = 'Origin'
    return response

@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return add_cors(app.make_response(''))

@app.route('/')
def index():
    """Root route — HF Spaces and browsers probe GET / (avoids 405/500 noise)."""
    return jsonify({
        'service': 'ETIB Interpreter Trainer API',
        'status': 'ok',
        'docs': 'Backend for https://etib-interpreter-trainer.vercel.app — see /health and /api/config',
    })

# Ensure output directories exist at startup
os.makedirs(os.getenv('UPLOAD_FOLDER', './uploads'), exist_ok=True)
os.makedirs(os.getenv('AUDIO_OUTPUT_FOLDER', './audio_outputs'), exist_ok=True)

# ── Register module blueprints ──────────────────────────────────────────────
from modules.module_a import module_a_bp
from modules.module_b import module_b_bp
from modules.module_c import module_c_bp
from modules.module_d import module_d_bp
from modules.module_library import module_library_bp
from modules.auth import auth_bp
from modules.chat import chat_bp

app.register_blueprint(module_a_bp,       url_prefix='/api/module-a')
app.register_blueprint(module_b_bp,       url_prefix='/api/module-b')
app.register_blueprint(module_c_bp,       url_prefix='/api/module-c')
app.register_blueprint(module_d_bp,       url_prefix='/api/module-d')
app.register_blueprint(module_library_bp, url_prefix='/api/library')
app.register_blueprint(auth_bp,           url_prefix='/api/auth')
app.register_blueprint(chat_bp,           url_prefix='/api/chat')

# ── Per-request Groq key from frontend ──────────────────────────────────────
@app.before_request
def extract_request_context():
    payload = request.get_json(silent=True) or {}
    key = (
        request.headers.get('X-Groq-Api-Key', '') or
        payload.get('groq_api_key', '') or
        request.form.get('groq_api_key', '')
    ).strip()
    g.groq_api_key = key if key.startswith('gsk_') else None


# ── Health check ────────────────────────────────────────────────────────────
@app.route('/health')
def health():
    """Basic health check. Returns 200 if server is running."""
    return jsonify({
        'status': 'ok',
        'version': '0.1.0',
        'message': 'ETIB API is running'
    })

@app.route('/api/config')
def get_config():
    """Return available options for frontend dropdowns."""
    return jsonify({
        'languages': ['ar', 'fr', 'en'],
        'target_languages': ['ar', 'fr', 'en'],
        'domains': [
            'politics', 'diplomacy', 'economics', 'climate', 'health',
            'human rights', 'education', 'technology', 'migration',
            'disarmament', 'women', 'food'
        ],
        'terminology_densities': ['low', 'medium', 'high'],
        'difficulties': ['beginner', 'intermediate', 'advanced'],
        'structures': ['well-organized', 'semi-structured', 'deliberately disorganized'],
        'scenarios': [
            'UN General Assembly', 'EU Parliament', 'Arab League summit',
            'press conference', 'diplomatic meeting', 'political debate', 'interview'
        ],
        'modes': ['sight_translation', 'consecutive', 'simultaneous'],
        'speed_pressures': ['normal', 'fast', 'very_fast'],
        'topic_shifts': ['none', 'mild', 'frequent'],
        'cognitive_loads': ['low', 'medium', 'high'],
        'llm_provider': LLM_PROVIDER,
        'local_model_id': LOCAL_MODEL_ID,
        'remote_aya_configured': bool(REMOTE_AYA_URL and 'PASTE_' not in REMOTE_AYA_URL)
    })

@app.errorhandler(413)
def too_large(_):
    return jsonify({'error': 'File too large. Maximum upload size is 50 MB.'}), 413

@app.errorhandler(Exception)
def handle_exception(_):
    """Return JSON for all unhandled errors so the browser gets CORS headers."""
    import traceback
    traceback.print_exc()
    return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true', port=port, host='0.0.0.0', use_reloader=False)
