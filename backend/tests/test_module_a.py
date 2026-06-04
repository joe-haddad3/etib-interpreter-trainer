"""Tests for Module A - LLM Speech Generation."""
import json

import pytest

from app import app
from modules import module_a


def fake_generation(script: str = ' '.join(['word'] * 80)) -> str:
    return json.dumps({
        'script': script,
        'summary': 'Short summary.',
        'mcqs': [
            {
                'question': 'What is the main topic?',
                'options': ['Climate', 'Sports', 'Music', 'Travel'],
                'answer': 'Climate',
            }
        ],
        'glossary': [
            {
                'term': 'climate finance',
                'arabic': 'تمويل المناخ',
                'french': 'financement climatique',
                'english': 'climate finance',
                'definition': 'Funding for climate action.',
            }
        ],
        'metadata': {'pressure_factors': []},
    })


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json['status'] == 'ok'


def test_generate_english_speech(client, monkeypatch):
    monkeypatch.setattr(module_a, 'generate_text', lambda **kwargs: fake_generation())

    res = client.post('/api/module-a/generate',
        json={'topic': 'Climate finance', 'language': 'en', 'target_language': 'fr',
              'domain': 'climate', 'word_count': 100})

    assert res.status_code == 200
    data = res.json
    assert data['script']
    assert data['summary'] == 'Short summary.'
    assert data['mcqs'][0]['answer'] == 'Climate'
    assert data['glossary'][0]['french'] == 'financement climatique'
    assert data['word_count'] > 50
    assert data['language'] == 'en'
    assert data['target_language'] == 'fr'
    assert data['topic'] == 'Climate finance'


def test_generate_french_speech(client, monkeypatch):
    monkeypatch.setattr(module_a, 'generate_text', lambda **kwargs: fake_generation(' '.join(['mot'] * 80)))

    res = client.post('/api/module-a/generate',
        json={'topic': 'Diplomatie regionale', 'language': 'fr', 'target_language': 'ar',
              'domain': 'diplomacy', 'word_count': 100})

    assert res.status_code == 200
    assert res.json['language'] == 'fr'
    assert res.json['target_language'] == 'ar'


def test_generate_arabic_speech(client, monkeypatch):
    monkeypatch.setattr(module_a, 'generate_text', lambda **kwargs: fake_generation(' '.join(['خطاب'] * 80)))

    res = client.post('/api/module-a/generate',
        json={'topic': 'الصحة العامة', 'language': 'ar', 'target_language': 'en',
              'domain': 'health', 'word_count': 150, 'scenario': 'Arab League summit'})

    assert res.status_code == 200
    data = res.json
    assert data['language'] == 'ar'
    assert data['target_language'] == 'en'
    arabic_chars = [c for c in data['script'] if '\u0600' <= c <= '\u06FF']
    assert len(arabic_chars) > 20


def test_pressure_metadata(client, monkeypatch):
    monkeypatch.setattr(module_a, 'generate_text', lambda **kwargs: fake_generation())

    res = client.post('/api/module-a/generate',
        json={'topic': 'Economic recovery', 'language': 'en', 'target_language': 'fr',
              'domain': 'economics', 'word_count': 100, 'pressure_enabled': True,
              'speed_pressure': 'fast', 'topic_shifts': 'mild', 'context_noise': True,
              'cognitive_load': 'high'})

    assert res.status_code == 200
    metadata = res.json['metadata']
    assert metadata['pressure_enabled'] is True
    assert metadata['pressure_settings']['speed_pressure'] == 'fast'
    assert metadata['pressure_settings']['context_noise'] is True


def test_invalid_language(client):
    res = client.post('/api/module-a/generate',
        json={'topic': 'Climate', 'language': 'de', 'domain': 'climate'})
    assert res.status_code == 400


def test_invalid_target_language(client):
    res = client.post('/api/module-a/generate',
        json={'topic': 'Climate', 'language': 'en', 'target_language': 'de', 'domain': 'climate'})
    assert res.status_code == 400


def test_missing_topic(client):
    res = client.post('/api/module-a/generate',
        json={'language': 'en', 'target_language': 'fr', 'domain': 'climate'})
    assert res.status_code == 400


def test_invalid_word_count(client):
    res = client.post('/api/module-a/generate',
        json={'topic': 'Climate', 'language': 'en', 'target_language': 'fr',
              'domain': 'climate', 'word_count': 20})
    assert res.status_code == 400


def test_missing_body(client):
    res = client.post('/api/module-a/generate',
        content_type='application/json', data='')
    assert res.status_code == 400
