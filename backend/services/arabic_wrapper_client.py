"""
Arabic evaluation micro-service client
======================================
Thin HTTP client for Ali's Arabic FastAPI wrapper (the `new_arabic_solution`
branch). It calls the wrapper's `/api/arabic-wrapper/evaluate` endpoint with the
student's audio + Arabic reference text and returns the JSON result.

Design goals:
- **Independence:** this Flask backend never imports the FastAPI code or loads
  the heavy wav2vec2 / Silero models. The two apps only talk over HTTP.
- **Opt-in:** does nothing unless ARABIC_WRAPPER_URL is configured.
- **Fail-open:** any error (unconfigured, unreachable, timeout, bad response)
  returns None so the existing evaluation is never broken.

Contract reference: ARABIC_WRAPPER_API.md on the new_arabic_solution branch.
"""
import os

import requests

from config import (
    ARABIC_WRAPPER_URL,
    ARABIC_WRAPPER_API_KEY,
    ARABIC_WRAPPER_TIMEOUT,
)


def is_configured() -> bool:
    """True only when an Arabic wrapper URL has been provided."""
    return bool(ARABIC_WRAPPER_URL)


def evaluate_arabic(
    audio_path: str,
    reference_text: str = '',
    mode: str = 'auto',
    exercise_id: str = '',
) -> dict | None:
    """
    Send audio + Arabic reference to the wrapper and return its JSON result.

    audio_path      path to a decodable audio file (webm/wav/m4a/mp3).
    reference_text  Arabic reference; empty => wrapper falls back to 'light' mode.
    mode            'auto' | 'light' | 'full' (see ARABIC_WRAPPER_API.md).
    exercise_id     optional identifier passed through to the wrapper.

    Returns the parsed JSON dict, or None on any failure (fail-open).
    """
    if not ARABIC_WRAPPER_URL:
        return None

    url = ARABIC_WRAPPER_URL.rstrip('/') + '/api/arabic-wrapper/evaluate'
    headers = {}
    if ARABIC_WRAPPER_API_KEY:
        headers['X-API-Key'] = ARABIC_WRAPPER_API_KEY

    try:
        with open(audio_path, 'rb') as fh:
            files = {
                'audio': (os.path.basename(audio_path) or 'student.webm', fh, 'audio/webm'),
            }
            data = {
                'reference_text': reference_text or '',
                'mode': mode,
                'exercise_id': exercise_id or '',
            }
            resp = requests.post(
                url,
                files=files,
                data=data,
                headers=headers,
                timeout=ARABIC_WRAPPER_TIMEOUT,
            )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: BLE001 — must never break the main evaluation
        print(f'[arabic_wrapper] call failed (non-fatal): {exc}')
        return None
