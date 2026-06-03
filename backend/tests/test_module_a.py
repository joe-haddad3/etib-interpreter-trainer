"""
Tests for Module A — LLM Speech Generation
============================================
Run with: pytest tests/test_module_a.py -v
"""
import pytest
import json
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json['status'] == 'ok'


def test_generate_english_speech(client):
    res = client.post('/api/module-a/generate',
        json={'language': 'en', 'domain': 'climate', 'word_count': 100})
    assert res.status_code == 200
    data = res.json
    assert 'script' in data
    assert data['word_count'] > 50
    assert data['language'] == 'en'


def test_generate_french_speech(client):
    res = client.post('/api/module-a/generate',
        json={'language': 'fr', 'domain': 'diplomacy', 'word_count': 100})
    assert res.status_code == 200
    assert res.json['language'] == 'fr'


def test_generate_arabic_speech(client):
    """Critical test — Arabic is the primary language of this project."""
    res = client.post('/api/module-a/generate',
        json={'language': 'ar', 'domain': 'health', 'word_count': 150,
              'scenario': 'Arab League summit'})
    assert res.status_code == 200
    data = res.json
    assert 'script' in data
    assert data['language'] == 'ar'
    # Check that Arabic characters are present in the output
    arabic_chars = [c for c in data['script'] if '\u0600' <= c <= '\u06FF']
    assert len(arabic_chars) > 20, \
        f"Expected Arabic script, got: {data['script'][:200]}"


def test_invalid_language(client):
    res = client.post('/api/module-a/generate',
        json={'language': 'de', 'domain': 'climate'})
    assert res.status_code == 400


def test_missing_body(client):
    res = client.post('/api/module-a/generate',
        content_type='application/json', data='')
    assert res.status_code == 400
