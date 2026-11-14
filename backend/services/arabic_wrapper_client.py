"""
Arabic evaluation micro-service client (Ali's "Sawt" Space)
===========================================================
Calls Ali's Arabic i'rab / tashkeel service, hosted as a Gradio app on a
Hugging Face ZeroGPU Space (default: Ali-Alii/sawt-arabic-gpu, endpoint
`/evaluate`). Contract: docs/INTEGRATION.md in Ali-Alii/interpreter_arabic_system.

We speak Gradio's plain HTTP API with `requests` instead of installing
`gradio_client`: that package needs huggingface-hub>=1.16, which can clash
with the speech stack (whisperx/transformers). The protocol is three calls:
  1. POST /gradio_api/upload                    -> server-side file path
  2. POST /gradio_api/call/evaluate              -> event_id
  3. GET  /gradio_api/call/evaluate/<event_id>   -> server-sent events
                                                    (complete | error)

Design goals:
- **Opt-in:** does nothing unless ARABIC_WRAPPER_URL is configured.
- **Fail-open:** never raises. On success returns Ali's JSON; when the check
  cannot run (too long, quota, timeout, service down) returns a small dict with
  `pronunciation.available = False` and an `unavailable` reason, so the report
  can say WHY instead of silently skipping. The main evaluation is unaffected.
- **Quota:** ZeroGPU time is charged to the account whose token we send
  (HF_TOKEN). Without a token the anonymous quota is tiny.
"""
import mimetypes
import os
import time
import wave

import requests

from config import ARABIC_WRAPPER_URL, ARABIC_WRAPPER_TIMEOUT, HF_TOKEN

# Limits published by Ali's service (INTEGRATION.md).
MAX_SECONDS = 120.0
MIN_SECONDS = 0.3
MAX_BYTES = 25 * 1024 * 1024
API_NAME = 'evaluate'


def is_configured() -> bool:
    """True only when the Arabic service location has been provided."""
    return bool(ARABIC_WRAPPER_URL)


def space_base_url(value: str) -> str:
    """Accept either a Space id ('Ali-Alii/sawt-arabic-gpu') or a URL."""
    value = (value or '').strip().rstrip('/')
    if not value:
        return ''
    if value.startswith(('http://', 'https://')):
        return value
    sub = value.lower().replace('/', '-').replace('_', '-').replace('.', '-')
    return f'https://{sub}.hf.space'


def _unavailable(code: str, message: str, **extra) -> dict:
    return {
        'pronunciation': {'available': False},
        'unavailable': {'code': code, 'message': message, **extra},
    }


def _wav_duration(path: str) -> float | None:
    """Duration of a WAV file (callers pass the normalised 16 kHz WAV)."""
    try:
        with wave.open(path, 'rb') as w:
            return w.getnframes() / float(w.getframerate() or 1)
    except Exception:
        return None  # not a WAV — let the service enforce its own limit


def _headers() -> dict:
    # Same header gradio_client sends; the Space proxy uses it to charge
    # ZeroGPU time to this account instead of the anonymous quota.
    return {'x-hf-authorization': f'Bearer {HF_TOKEN}'} if HF_TOKEN else {}


def _classify_error(text: str) -> dict:
    low = (text or '').lower()
    if 'zerogpu' in low or 'quota' in low or 'runs limit' in low:
        return _unavailable('quota', 'Daily GPU quota for the Arabic check is used up.', detail=text[:300])
    if '120' in low and ('second' in low or 'long' in low):
        return _unavailable('too_long', 'Recording is longer than the 2-minute limit of the Arabic check.', detail=text[:300])
    return _unavailable('error', 'The Arabic check service returned an error.', detail=text[:300])


def _read_events(base: str, event_id: str, deadline: float) -> dict:
    """Read the SSE stream until 'complete' or 'error' (bounded by deadline)."""
    import json

    url = f'{base}/gradio_api/call/{API_NAME}/{event_id}'
    event = None
    with requests.get(url, headers=_headers(), stream=True,
                      timeout=(15, 60)) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if time.monotonic() > deadline:
                return _unavailable('timeout', 'The Arabic check took too long.')
            if not line:
                continue
            if line.startswith('event:'):
                event = line[6:].strip()
            elif line.startswith('data:'):
                data = line[5:].strip()
                if event == 'complete':
                    out = json.loads(data)
                    result = out[0] if isinstance(out, list) and out else out
                    if isinstance(result, dict):
                        return result
                    return _unavailable('error', 'Unexpected response from the Arabic check.')
                if event == 'error':
                    try:
                        msg = (json.loads(data) or {}).get('error') or data
                    except Exception:
                        msg = data
                    return _classify_error(str(msg))
    return _unavailable('error', 'The Arabic check ended without a result.')


def evaluate_arabic(
    audio_path: str,
    reference_text: str = '',
    mode: str = 'light',
    exercise_id: str = '',  # kept for call-site compatibility; unused
) -> dict | None:
    """
    Send audio + Arabic reference to Ali's service.

    mode 'light' -> vocalised transcript only; 'full' -> plus per-word i'rab
    findings against reference_text.

    Returns None when the service is not configured, otherwise a dict (Ali's
    result, or an `unavailable` stub — see module docstring). Never raises.
    """
    base = space_base_url(ARABIC_WRAPPER_URL)
    if not base:
        return None

    try:
        size = os.path.getsize(audio_path)
        if size > MAX_BYTES:
            return _unavailable('too_large', 'Recording is larger than the 25 MB limit of the Arabic check.')
        seconds = _wav_duration(audio_path)
        if seconds is not None and seconds > MAX_SECONDS:
            return _unavailable(
                'too_long',
                'Recording is longer than the 2-minute limit of the Arabic check.',
                duration_seconds=round(seconds, 1), max_seconds=MAX_SECONDS,
            )
        if seconds is not None and seconds < MIN_SECONDS:
            return _unavailable('too_short', 'Recording is too short for the Arabic check.')

        deadline = time.monotonic() + ARABIC_WRAPPER_TIMEOUT
        name = os.path.basename(audio_path) or 'student.wav'
        ctype = mimetypes.guess_type(name)[0] or 'application/octet-stream'

        with open(audio_path, 'rb') as fh:
            up = requests.post(f'{base}/gradio_api/upload', headers=_headers(),
                               files=[('files', (name, fh, ctype))], timeout=60)
        up.raise_for_status()
        server_path = up.json()[0]

        payload = {'data': [
            {'path': server_path, 'orig_name': name, 'meta': {'_type': 'gradio.FileData'}},
            reference_text or '',
            mode if mode in ('light', 'full') else 'light',
        ]}
        start = requests.post(f'{base}/gradio_api/call/{API_NAME}', headers=_headers(),
                              json=payload, timeout=30)
        start.raise_for_status()
        return _read_events(base, start.json()['event_id'], deadline)
    except requests.Timeout:
        print('[arabic_wrapper] timeout (non-fatal)')
        return _unavailable('timeout', 'The Arabic check took too long.')
    except Exception as exc:  # noqa: BLE001 — must never break the main evaluation
        print(f'[arabic_wrapper] call failed (non-fatal): {exc}')
        return _unavailable('error', 'The Arabic check service could not be reached.')
