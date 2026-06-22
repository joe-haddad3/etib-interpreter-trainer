"""
Groq client factory.

Returns a Groq client using the per-request key sent by the frontend
(X-Groq-Api-Key header, stored in flask.g), falling back to the
server-level GROQ_API_KEY from .env.
"""
from config import GROQ_API_KEY

_server_client = None  # cached only for the server key


def get_groq_key() -> str | None:
    """Active Groq API key: per-request (user) key → server key → None."""
    try:
        from flask import g
        if getattr(g, 'groq_api_key', None):
            return g.groq_api_key
    except RuntimeError:
        pass
    return GROQ_API_KEY


def get_groq_client():
    """Return a ready Groq client. Raises RuntimeError if no key is available."""
    global _server_client
    from groq import Groq

    key = get_groq_key()
    if not key:
        raise RuntimeError(
            'No Groq API key found. Add your personal key in Settings '
            'or ask the administrator to configure GROQ_API_KEY on the server.'
        )

    # Cache only when using the server key — user keys must create a fresh client
    if key == GROQ_API_KEY:
        if _server_client is None:
            _server_client = Groq(api_key=key)
        return _server_client

    return Groq(api_key=key)
