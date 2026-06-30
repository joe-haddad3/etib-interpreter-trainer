"""
Groq client factory.

Each student can supply their own Groq API key via the Settings modal
(stored in their browser, sent with every request). If they haven't,
the server falls back to a shared default key (GROQ_API_KEY env var)
when one is configured, so the platform works out of the box for
demos/testing without forcing every visitor to create a Groq account.
"""

_client_cache: dict = {}  # key -> Groq client


def get_groq_key() -> str | None:
    """Return the per-request user key, falling back to the server default key."""
    try:
        from flask import g
        key = getattr(g, 'groq_api_key', None)
        if key:
            return key
    except RuntimeError:
        pass
    from config import GROQ_API_KEY
    return GROQ_API_KEY or None


def get_groq_client():
    """Return a Groq client for the current request's key (user key or server default).

    Raises RuntimeError if neither a user key nor a server default key is configured.
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
