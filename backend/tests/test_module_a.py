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


def test_glossary_key_variants_are_normalized():
    raw = json.dumps({
        'script': ' '.join(['word'] * 80),
        'glossary': [
            {
                'term': 'adaptation grants',
                'Arabic': 'منح التكيف',
                'French': "subventions d'adaptation",
                'English': 'adaptation grants',
                'meaning': 'Grant funding for adaptation projects.',
            }
        ],
    })

    parsed = module_a.parse_generation_output(raw)

    assert parsed['glossary'][0]['arabic'] == 'منح التكيف'
    assert parsed['glossary'][0]['french'] == "subventions d'adaptation"
    assert parsed['glossary'][0]['english'] == 'adaptation grants'
    assert parsed['glossary'][0]['definition'] == 'Grant funding for adaptation projects.'


def test_fenced_json_output_is_parsed():
    raw = """```json
{
  "script": "Generated speech text",
  "summary": "Generated summary",
  "mcqs": [],
  "glossary": [
    {
      "term": "early warning systems",
      "arabic": "نظم الإنذار المبكر",
      "french": "systèmes d'alerte précoce",
      "english": "early warning systems",
      "definition": "Systems that warn communities before hazards occur."
    }
  ]
}
```"""

    parsed = module_a.parse_generation_output(raw)

    assert parsed['script'] == 'Generated speech text'
    assert parsed['summary'] == 'Generated summary'
    assert parsed['glossary'][0]['arabic'] == 'نظم الإنذار المبكر'


def test_python_like_dict_output_is_parsed():
    raw = """Here is the JSON:
{'script': 'Generated speech text', 'summary': 'Generated summary', 'mcqs': [], 'glossary': [{'term': 'debt relief', 'Arabic': 'تخفيف عبء الدين', 'French': 'allègement de la dette', 'English': 'debt relief'}]}"""

    parsed = module_a.parse_generation_output(raw)

    assert parsed['script'] == 'Generated speech text'
    assert parsed['summary'] == 'Generated summary'
    assert parsed['glossary'][0]['arabic'] == 'تخفيف عبء الدين'


def test_json_with_raw_newlines_inside_script_is_parsed():
    raw = """{
  "script": "Mesdames et Messieurs,

Je me tiens devant vous aujourd'hui.",
  "summary": "Résumé court.",
  "mcqs": [
    {
      "question": "Quel est le sujet?",
      "options": ["Climat", "Sport", "Musique", "Voyage"],
      "answer": "Climat"
    }
  ],
  "glossary": [
    {
      "term": "Changement climatique",
      "arabic": "تغير المناخ",
      "french": "Changement climatique",
      "english": "Climate change",
      "definition": "Modification durable du climat."
    }
  ]
}"""

    parsed = module_a.parse_generation_output(raw)

    assert parsed['script'].startswith('Mesdames et Messieurs')
    assert parsed['summary'] == 'Résumé court.'
    assert parsed['mcqs'][0]['answer'] == 'Climat'
    assert parsed['glossary'][0]['arabic'] == 'تغير المناخ'


def test_remote_aya_provider_payload(monkeypatch):
    from services import llm_service

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {'text': 'remote aya response'}

    def fake_post(url, headers, json, timeout, verify):
        captured['url'] = url
        captured['headers'] = headers
        captured['json'] = json
        captured['timeout'] = timeout
        captured['verify'] = verify
        return FakeResponse()

    monkeypatch.setattr(llm_service, 'REMOTE_AYA_URL', 'https://example.ngrok-free.app/generate')
    monkeypatch.setattr(llm_service, 'REMOTE_AYA_TIMEOUT_SECONDS', 123)
    monkeypatch.setattr(llm_service, 'REMOTE_AYA_VERIFY_SSL', False)
    monkeypatch.setattr('requests.post', fake_post)

    output = llm_service._generate_with_remote_aya(
        [{'role': 'user', 'content': 'hello'}],
        max_tokens=42,
        temperature=0.3,
    )

    assert output == 'remote aya response'
    assert captured['url'] == 'https://example.ngrok-free.app/generate'
    assert captured['headers']['ngrok-skip-browser-warning'] == 'true'
    assert captured['json']['max_tokens'] == 42
    assert captured['json']['temperature'] == 0.3
    assert captured['timeout'] == 123
    assert captured['verify'] is False


def test_remote_aya_http_error_includes_response_body(monkeypatch):
    from services import llm_service
    import pytest
    import requests

    class FakeResponse:
        status_code = 403
        text = 'ngrok blocked this request'

        def raise_for_status(self):
            raise requests.HTTPError('403 Client Error')

    def fake_post(url, headers, json, timeout, verify):
        return FakeResponse()

    monkeypatch.setattr(llm_service, 'REMOTE_AYA_URL', 'https://example.ngrok-free.app/generate')
    monkeypatch.setattr('requests.post', fake_post)

    with pytest.raises(RuntimeError) as exc_info:
        llm_service._generate_with_remote_aya(
            [{'role': 'user', 'content': 'hello'}],
            max_tokens=42,
            temperature=0.3,
        )

    message = str(exc_info.value)
    assert 'HTTP 403' in message
    assert 'ngrok blocked this request' in message


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
