"""
Groq client factory — per-student key mode.

Each student supplies their own Groq API key via the Settings modal.
The key is stored in their browser (localStorage) and sent with every
request as the X-Groq-Api-Key header.  There is NO server-level
fallback key; if no student key is present the call raises RuntimeError.
"""

_client_cache: dict = {}  # key -> Groq client


def get_groq_key() -> str | None:
    """Return the per-request user key, or None if not set."""
    try:
        from flask import g
        return getattr(g, 'groq_api_key', None)
    except RuntimeError:
        return None


def get_groq_client():
    """Return a Groq client for the current request's key.

    Raises RuntimeError if the student hasn't saved their key yet.
    """
    from groq import Groq

    key = get_groq_key()
    if not key:
        raise RuntimeError(
            'No Groq API key found. Please open Settings and add your '
            'personal Groq API key (free at console.groq.com).'
        )

    if key not in _client_cache:
        _client_cache[key] = Groq(api_key=key)
    return _client_cache[key]
