"""
Authentication endpoints for the ETIB platform.

Uses MongoDB when available; falls back to an in-memory store so the app
runs without a MongoDB installation during development.
Expected defaults:
  MONGODB_URI=mongodb://127.0.0.1:27017
  MONGODB_DB=etib_interpreter_trainer
"""
import os
import secrets
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash


auth_bp = Blueprint('auth', __name__)

# ── Token store ───────────────────────────────────────────────────────────────
# Tokens are stored HASHED (sha256): a database leak must not hand out live
# session tokens. The raw token exists only in the client's browser.
import hashlib

_tokens: dict = {}  # in-memory fallback: token_hash → email

def _hash_token(token: str) -> str:
    return hashlib.sha256(str(token or '').encode('utf-8')).hexdigest()

def _get_tokens_col():
    if _try_mongo():
        return _mongo_client[MONGODB_DB]['auth_tokens']
    return None

def create_token(user: dict) -> str:
    token = secrets.token_hex(32)
    token_hash = _hash_token(token)
    col = _get_tokens_col()
    if col is not None:
        col.update_one({'token': token_hash}, {'$set': {'token': token_hash, 'email': user['email']}}, upsert=True)
    else:
        _tokens[token_hash] = user['email']
    return token

def revoke_token(token: str) -> None:
    token_hash = _hash_token(token)
    col = _get_tokens_col()
    if col is not None:
        col.delete_one({'token': token_hash})
    else:
        _tokens.pop(token_hash, None)

def get_user_from_token(token: str):
    if not token:
        return None
    token_hash = _hash_token(token)
    col = _get_tokens_col()
    if col is not None:
        doc = col.find_one({'token': token_hash})
        email = doc['email'] if doc else None
    else:
        email = _tokens.get(token_hash)
    return find_user_by_email(email) if email else None

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017')
MONGODB_DB = os.getenv('MONGODB_DB', 'etib_interpreter_trainer')
VALID_ROLES = {'student', 'coordinator'}

# Demo accounts with publicly-known passwords are a security hole in
# production — anyone reading the repo can log into them. Only seeded when
# SEED_DEMO_USERS=true is set explicitly (local development).
_SEED_ENABLED = os.getenv('SEED_DEMO_USERS', '').strip().lower() in {'1', 'true', 'yes'}
SEED_USERS = [
    ('Demo Student', 'student@etib.edu', 'student', 'student123'),
    ('Demo Coordinator', 'coordinator@etib.edu', 'coordinator', 'coordinator123'),
] if _SEED_ENABLED else []

# ── Storage backend (MongoDB or in-memory fallback) ──────────────────────────

_mongo_client = None
_use_mongo = None          # None = not yet decided
_auth_initialized = False

# In-memory fallback: { email: user_dict }
_mem_users: dict = {}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def _try_mongo():
    """Return True if MongoDB is reachable, False otherwise."""
    global _mongo_client, _use_mongo
    # If already connected, reuse the client
    if _use_mongo is True:
        return True
    # Always retry if previous attempt failed (don't permanently cache False)
    try:
        from pymongo import MongoClient
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=8000)
        client.admin.command('ping')
        _mongo_client = client
        _use_mongo = True
        print('[Auth] MongoDB connected.')
    except Exception as exc:
        _use_mongo = None  # allow retry next request
        print(f'[Auth] MongoDB not available ({exc}) — using in-memory store (data resets on restart).')
        return False
    return _use_mongo


def get_users_collection():
    from pymongo import ASCENDING
    return _mongo_client[MONGODB_DB]['users']


def init_auth_db():
    global _auth_initialized
    if _auth_initialized:
        return

    if _try_mongo():
        from pymongo import ASCENDING
        users = get_users_collection()
        users.create_index([('email', ASCENDING)], unique=True)
        for name, email, role, password in SEED_USERS:
            users.update_one(
                {'email': email},
                {'$setOnInsert': {
                    'id': f'user-{uuid.uuid4().hex}',
                    'name': name, 'email': email, 'role': role,
                    'password_hash': generate_password_hash(password),
                    'created_at': utc_now(),
                }},
                upsert=True
            )
    else:
        for name, email, role, password in SEED_USERS:
            if email not in _mem_users:
                _mem_users[email] = {
                    'id': f'user-{uuid.uuid4().hex}',
                    'name': name, 'email': email, 'role': role,
                    'password_hash': generate_password_hash(password),
                    'created_at': utc_now(),
                }

    _auth_initialized = True


def public_user(user):
    return {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'role': user['role'],
    }


def find_user_by_email(email):
    init_auth_db()
    if _try_mongo():
        return get_users_collection().find_one({'email': email})
    return _mem_users.get(email)


def validate_signup_payload(payload):
    name = (payload.get('name') or '').strip()
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password') or ''
    role = payload.get('role') or 'student'

    if not name:
        return None, 'Name is required'
    if not email or '@' not in email:
        return None, 'A valid email is required'
    if len(password) < 8:
        return None, 'Password must be at least 8 characters'
    if role not in VALID_ROLES:
        return None, 'Invalid role'

    return {
        'name': name,
        'email': email,
        'password': password,
        'role': role,
    }, None


@auth_bp.route('/signup', methods=['POST'])
def signup():
    payload = request.get_json(silent=True) or {}
    user_data, error = validate_signup_payload(payload)
    if error:
        return jsonify({'error': error}), 400

    init_auth_db()
    user = {
        'id': f'user-{uuid.uuid4().hex}',
        'name': user_data['name'],
        'email': user_data['email'],
        'role': user_data['role'],
        'password_hash': generate_password_hash(user_data['password']),
        'created_at': utc_now(),
    }

    if _try_mongo():
        from pymongo.errors import DuplicateKeyError
        try:
            get_users_collection().insert_one(user)
        except DuplicateKeyError:
            return jsonify({'error': 'An account with this email already exists'}), 409
    else:
        if user_data['email'] in _mem_users:
            return jsonify({'error': 'An account with this email already exists'}), 409
        _mem_users[user_data['email']] = user

    token = create_token(user)
    return jsonify({
        'user': public_user(user),
        'token': token,
        'message': 'Signup successful',
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password') or ''
    requested_role = payload.get('role')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = find_user_by_email(email)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401

    if requested_role and requested_role != user['role']:
        return jsonify({'error': 'Selected role does not match this account'}), 403

    token = create_token(user)
    return jsonify({
        'user': public_user(user),
        'token': token,
        'message': 'Login successful',
    })


@auth_bp.route('/me', methods=['GET'])
def me():
    token = request.args.get('auth_token', '').strip()
    user = get_user_from_token(token)
    if not user:
        return jsonify({'authenticated': False}), 401
    return jsonify({'authenticated': True, 'user': public_user(user)})


@auth_bp.route('/logout', methods=['POST'])
def logout():
    payload = request.get_json(silent=True) or {}
    token = payload.get('auth_token', '').strip()
    revoke_token(token)
    return jsonify({'message': 'Logout successful'})


@auth_bp.route('/validate-groq-key', methods=['POST'])
def validate_groq_key():
    """Test a Groq API key by making a minimal chat completion call."""
    payload = request.get_json(silent=True) or {}
    key = (payload.get('api_key') or '').strip()

    if not key:
        return jsonify({'valid': False, 'error': 'No key provided'}), 400
    if not key.startswith('gsk_'):
        return jsonify({'valid': False, 'error': 'Groq keys must start with gsk_'}), 400

    try:
        from groq import Groq
        client = Groq(api_key=key)
        client.chat.completions.create(
            model='llama-3.1-8b-instant',
            messages=[{'role': 'user', 'content': 'Hi'}],
            max_tokens=1,
        )
        return jsonify({'valid': True})
    except Exception as exc:
        msg = str(exc)
        if 'invalid_api_key' in msg.lower() or '401' in msg:
            return jsonify({'valid': False, 'error': 'Invalid API key'}), 200
        return jsonify({'valid': False, 'error': f'Could not verify: {msg[:120]}'}), 200
