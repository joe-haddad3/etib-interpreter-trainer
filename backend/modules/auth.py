"""
Authentication endpoints for the ETIB platform.

Uses MongoDB for local development and production-like account persistence.
Expected defaults:
  MONGODB_URI=mongodb://127.0.0.1:27017
  MONGODB_DB=etib_interpreter_trainer
"""
import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, session
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError
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

_mongo_client = None
_auth_initialized = False


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def get_mongo_client():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
    return _mongo_client


def get_users_collection():
    client = get_mongo_client()
    return client[MONGODB_DB]['users']


def init_auth_db():
    global _auth_initialized
    if _auth_initialized:
        return

    users = get_users_collection()
    try:
        users.database.client.admin.command('ping')
    except ServerSelectionTimeoutError as exc:
        raise RuntimeError('MongoDB is not reachable at MONGODB_URI') from exc

    users.create_index([('email', ASCENDING)], unique=True)
    for name, email, role, password in SEED_USERS:
        users.update_one(
            {'email': email},
            {
                '$setOnInsert': {
                    'id': f'user-{uuid.uuid4().hex}',
                    'name': name,
                    'email': email,
                    'role': role,
                    'password_hash': generate_password_hash(password),
                    'created_at': utc_now(),
                }
            },
            upsert=True
        )

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
    return get_users_collection().find_one({'email': email})


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
    users = get_users_collection()
    user = {
        'id': f'user-{uuid.uuid4().hex}',
        'name': user_data['name'],
        'email': user_data['email'],
        'role': user_data['role'],
        'password_hash': generate_password_hash(user_data['password']),
        'created_at': utc_now(),
    }

    try:
        users.insert_one(user)
    except DuplicateKeyError:
        return jsonify({'error': 'An account with this email already exists'}), 409

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
