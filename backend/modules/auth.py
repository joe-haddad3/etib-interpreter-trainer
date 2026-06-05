"""
Authentication endpoints for the ETIB platform.

Uses MongoDB when available; falls back to an in-memory store so the app
runs without a MongoDB installation during development.
Expected defaults:
  MONGODB_URI=mongodb://127.0.0.1:27017
  MONGODB_DB=etib_interpreter_trainer
"""
import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash


auth_bp = Blueprint('auth', __name__)

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017')
MONGODB_DB = os.getenv('MONGODB_DB', 'etib_interpreter_trainer')
VALID_ROLES = {'student', 'instructor', 'coordinator'}

SEED_USERS = [
    ('Demo Student', 'student@etib.edu', 'student', 'student123'),
    ('Demo Instructor', 'instructor@etib.edu', 'instructor', 'instructor123'),
    ('Demo Coordinator', 'coordinator@etib.edu', 'coordinator', 'coordinator123'),
]

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
    if _use_mongo is not None:
        return _use_mongo
    try:
        from pymongo import MongoClient
        from pymongo.errors import ServerSelectionTimeoutError
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        _mongo_client = client
        _use_mongo = True
        print('[Auth] MongoDB connected.')
    except Exception:
        _use_mongo = False
        print('[Auth] MongoDB not available — using in-memory store (data resets on restart).')
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


def set_user_session(user):
    session['user_id'] = user['id']
    session['email'] = user['email']


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

    set_user_session(user)
    return jsonify({
        'user': public_user(user),
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

    set_user_session(user)

    return jsonify({
        'user': public_user(user),
        'message': 'Login successful',
    })


@auth_bp.route('/me', methods=['GET'])
def me():
    email = session.get('email')
    user = find_user_by_email(email) if email else None
    if not user:
        return jsonify({'authenticated': False}), 401

    return jsonify({
        'authenticated': True,
        'user': public_user(user),
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful'})
