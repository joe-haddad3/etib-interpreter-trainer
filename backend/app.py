"""
ETIB Interpreter Self-Training Platform — Flask Backend
=======================================================
Entry point. Registers all module blueprints and starts the server.

Run with:
    cd backend
    python app.py
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv(override=True)

from config import LLM_PROVIDER, LOCAL_MODEL_ID, REMOTE_AYA_URL

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-in-prod')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
CORS(app, supports_credentials=True, origins=[
    'http://127.0.0.1:5174',
    'http://localhost:5174',
    'http://127.0.0.1:5173',
    'http://localhost:5173',
])

# Ensure output directories exist at startup
os.makedirs(os.getenv('UPLOAD_FOLDER', './uploads'), exist_ok=True)
os.makedirs(os.getenv('AUDIO_OUTPUT_FOLDER', './audio_outputs'), exist_ok=True)

# ── Register module blueprints ──────────────────────────────────────────────
from modules.module_a import module_a_bp
from modules.module_b import module_b_bp
from modules.module_c import module_c_bp
from modules.module_d import module_d_bp
from modules.auth import auth_bp

app.register_blueprint(module_a_bp, url_prefix='/api/module-a')
app.register_blueprint(module_b_bp, url_prefix='/api/module-b')
app.register_blueprint(module_c_bp, url_prefix='/api/module-c')
app.register_blueprint(module_d_bp, url_prefix='/api/module-d')
app.register_blueprint(auth_bp, url_prefix='/api/auth')

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
            'politics', 'diplomacy', 'economics',
            'climate', 'health', 'human rights', 'education'
        ],
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

@app.errorhandler(Exception)
def handle_exception(e):
    """Return JSON for all unhandled errors so the browser gets CORS headers."""
    import traceback
    traceback.print_exc()
    return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'true').lower() == 'true', port=5000)
