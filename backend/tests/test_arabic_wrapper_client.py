"""Tests for the Arabic i'rab service client (Ali's Gradio ZeroGPU Space).

The network is mocked: these check our side of the contract (upload ->
call -> event stream, limits, fail-open), not Ali's model.
"""
import json
import wave

import pytest

from services import arabic_wrapper_client as client


def _wav(path, seconds, rate=16000):
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b'\x00\x00' * int(seconds * rate))
    return str(path)


class _Resp:
    def __init__(self, payload=None, lines=None, status=200):
        self._payload, self._lines, self.status_code = payload, lines or [], status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise client.requests.HTTPError(f'HTTP {self.status_code}')

    def json(self):
        return self._payload

    def iter_lines(self, decode_unicode=True):
        yield from self._lines

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


ALI_RESULT = {
    'schema_version': '1.0', 'mode': 'full',
    'transcript': {'diacritized': 'ذهبَ الطالبُ'},
    'pronunciation': {'available': True,
                      'summary': {'correct': 2, 'incorrect': 0, 'uncertain': 0, 'accuracy': 1.0},
                      'findings': [{'word': 'ذهبَ', 'status': 'correct',
                                    'expected_ending': 'fatha', 'detected_ending': 'fatha'}]},
}


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(client, 'ARABIC_WRAPPER_URL', 'Ali-Alii/sawt-arabic-gpu')
    monkeypatch.setattr(client, 'HF_TOKEN', 'hf_test_token')


def _mock_network(monkeypatch, events, calls):
    def fake_post(url, **kw):
        calls.append(('POST', url, kw.get('headers'), kw.get('json')))
        if url.endswith('/gradio_api/upload'):
            return _Resp(['/tmp/gradio/abc/student.wav'])
        return _Resp({'event_id': 'ev1'})

    def fake_get(url, **kw):
        calls.append(('GET', url, kw.get('headers'), None))
        return _Resp(lines=events)

    monkeypatch.setattr(client.requests, 'post', fake_post)
    monkeypatch.setattr(client.requests, 'get', fake_get)


def test_space_id_becomes_hf_space_url():
    assert client.space_base_url('Ali-Alii/sawt-arabic-gpu') == 'https://ali-alii-sawt-arabic-gpu.hf.space'
    assert client.space_base_url('https://x.hf.space/') == 'https://x.hf.space'
    assert client.space_base_url('') == ''


def test_not_configured_returns_none(monkeypatch, tmp_path):
    monkeypatch.setattr(client, 'ARABIC_WRAPPER_URL', '')
    assert client.is_configured() is False
    assert client.evaluate_arabic(_wav(tmp_path / 'a.wav', 2)) is None


def test_success_returns_ali_json_and_sends_token(configured, monkeypatch, tmp_path):
    calls = []
    _mock_network(monkeypatch, ['event: generating', 'data: null',
                                'event: complete', 'data: ' + json.dumps([ALI_RESULT])], calls)
    out = client.evaluate_arabic(_wav(tmp_path / 'a.wav', 3), reference_text='ذهبَ الطالبُ', mode='full')
    assert out == ALI_RESULT
    base = 'https://ali-alii-sawt-arabic-gpu.hf.space/gradio_api'
    assert [c[1] for c in calls] == [f'{base}/upload', f'{base}/call/evaluate', f'{base}/call/evaluate/ev1']
    assert all(c[2] == {'x-hf-authorization': 'Bearer hf_test_token'} for c in calls)
    data = calls[1][3]['data']
    assert data[0]['path'] == '/tmp/gradio/abc/student.wav'
    assert data[0]['meta'] == {'_type': 'gradio.FileData'}
    assert data[1:] == ['ذهبَ الطالبُ', 'full']


def test_quota_error_is_reported_not_raised(configured, monkeypatch, tmp_path):
    err = {'error': "'You have exceeded your ZeroGPU runs limit. Authenticate with a Hugging Face token'"}
    _mock_network(monkeypatch, ['event: error', 'data: ' + json.dumps(err)], [])
    out = client.evaluate_arabic(_wav(tmp_path / 'a.wav', 3), mode='light')
    assert out['pronunciation'] == {'available': False}
    assert out['unavailable']['code'] == 'quota'


def test_recording_over_two_minutes_is_skipped_without_network(configured, monkeypatch, tmp_path):
    def boom(*a, **k):
        raise AssertionError('network must not be called for a too-long recording')
    monkeypatch.setattr(client.requests, 'post', boom)
    out = client.evaluate_arabic(_wav(tmp_path / 'long.wav', 121, rate=8000), mode='full')
    assert out['unavailable']['code'] == 'too_long'
    assert out['unavailable']['duration_seconds'] == 121.0


def test_service_down_is_fail_open(configured, monkeypatch, tmp_path):
    def down(*a, **k):
        raise client.requests.ConnectionError('unreachable')
    monkeypatch.setattr(client.requests, 'post', down)
    out = client.evaluate_arabic(_wav(tmp_path / 'a.wav', 3), mode='full')
    assert out['unavailable']['code'] == 'error'


def test_unknown_mode_falls_back_to_light(configured, monkeypatch, tmp_path):
    calls = []
    _mock_network(monkeypatch, ['event: complete', 'data: ' + json.dumps([ALI_RESULT])], calls)
    client.evaluate_arabic(_wav(tmp_path / 'a.wav', 3), mode='auto')
    assert calls[1][3]['data'][2] == 'light'
