"""
Chat endpoint — AI assistant for interpretation training.
"""
from flask import Blueprint, jsonify, request, g
from services.llm_service import generate_text

chat_bp = Blueprint('chat', __name__)

SYSTEM_PROMPT = """You are ETIB Assistant, an AI coach specialized in conference interpretation training.
You help students and instructors using the ETIB Interpreter Self-Training Platform.

You can help with:
- Interpretation techniques (consecutive, simultaneous, sight translation)
- Tips for improving fluency, coverage, and accuracy
- Terminology in Arabic, French, and English
- How to use the platform features
- General questions about interpreting as a profession

Keep answers concise and practical. If asked something unrelated to interpretation or the platform,
politely redirect the conversation back to interpretation training."""


@chat_bp.route('/message', methods=['POST'])
def chat_message():
    payload = request.get_json(silent=True) or {}
    messages = payload.get('messages', [])
    if not messages:
        return jsonify({'error': 'messages array is required'}), 400

    if not g.groq_api_key:
        return jsonify({'error': 'Groq API key required. Please set it in the settings (⚙).'}), 400

    full_messages = [{'role': 'system', 'content': SYSTEM_PROMPT}] + messages[-20:]

    try:
        reply = generate_text(full_messages, max_tokens=400, temperature=0.7)
        return jsonify({'reply': reply.strip()})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500
