"""
Tests for authentication endpoints.
"""
import pytest
from app import app
from modules import auth


@pytest.fixture
def client():
    original_db = auth.MONGODB_DB
    auth.MONGODB_DB = 'etib_interpreter_trainer_test'
    auth._auth_initialized = False
    auth.get_users_collection().delete_many({})
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c
    auth.get_users_collection().delete_many({})
    auth.MONGODB_DB = original_db
    auth._auth_initialized = False


def test_login_success(client):
    res = client.post('/api/auth/login', json={
        'email': 'student@etib.edu',
        'password': 'student123',
        'role': 'student',
    })

    assert res.status_code == 200
    assert res.json['user']['email'] == 'student@etib.edu'
    assert res.json['user']['role'] == 'student'
    assert 'password_hash' not in res.json['user']


def test_login_invalid_password(client):
    res = client.post('/api/auth/login', json={
        'email': 'student@etib.edu',
        'password': 'wrong',
        'role': 'student',
    })

    assert res.status_code == 401


def test_login_role_mismatch(client):
    res = client.post('/api/auth/login', json={
        'email': 'student@etib.edu',
        'password': 'student123',
        'role': 'instructor',
    })

    assert res.status_code == 403


def test_signup_success(client):
    res = client.post('/api/auth/signup', json={
        'name': 'New Student',
        'email': 'new.student@example.com',
        'password': 'newpass123',
        'role': 'student',
    })

    assert res.status_code == 201
    assert res.json['user']['email'] == 'new.student@example.com'
    assert res.json['user']['name'] == 'New Student'
    assert 'password_hash' not in res.json['user']


def test_signup_duplicate_email(client):
    payload = {
        'name': 'New Student',
        'email': 'duplicate@example.com',
        'password': 'newpass123',
        'role': 'student',
    }
    first = client.post('/api/auth/signup', json=payload)
    second = client.post('/api/auth/signup', json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_me_after_login(client):
    client.post('/api/auth/login', json={
        'email': 'student@etib.edu',
        'password': 'student123',
        'role': 'student',
    })

    res = client.get('/api/auth/me')
    assert res.status_code == 200
    assert res.json['authenticated'] is True
    assert res.json['user']['email'] == 'student@etib.edu'
