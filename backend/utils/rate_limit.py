"""
Lightweight in-memory rate limiter.

Purpose: the chat assistant and the Groq-key validator are UNAUTHENTICATED and
fall back to the server's shared GROQ_API_KEY. Without a cap, anyone who knows
the public backend URL can drive the shared key (cost / quota exhaustion) — CORS
does not stop this, since CORS is a browser-only control and curl ignores it.

This is a per-process, per-IP fixed-window limiter. It is intentionally simple:
no external dependency, no Redis. On a single-container host (HF Spaces) that is
enough to stop trivial single-source abuse. It is NOT a defence against a large
distributed flood — pair it with a real gateway limit if that becomes a concern.

It fails OPEN: any internal error in the limiter lets the request through, so a
limiter bug can never take the API down.
"""
import time
import threading
from functools import wraps

from flask import request, jsonify

_lock = threading.Lock()
# key -> list[float] of request timestamps within the current window
_hits: dict[str, list[float]] = {}
_last_gc = 0.0


def _client_ip() -> str:
    # HF Spaces / proxies put the real client first in X-Forwarded-For.
    fwd = request.headers.get('X-Forwarded-For', '')
    if fwd:
        return fwd.split(',')[0].strip()
    return request.remote_addr or 'unknown'


def _gc(now: float, window: float) -> None:
    """Drop stale buckets so the dict cannot grow without bound."""
    global _last_gc
    if now - _last_gc < 60:
        return
    _last_gc = now
    for k in list(_hits.keys()):
        _hits[k] = [t for t in _hits[k] if now - t < window]
        if not _hits[k]:
            _hits.pop(k, None)


def rate_limit(max_requests: int, window_seconds: float, scope: str = 'default'):
    """Allow at most `max_requests` per `window_seconds` per client IP.

    Returns HTTP 429 when exceeded. Applied per-scope so different endpoints
    keep independent budgets.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                now = time.time()
                key = f'{scope}:{_client_ip()}'
                with _lock:
                    _gc(now, window_seconds)
                    bucket = [t for t in _hits.get(key, []) if now - t < window_seconds]
                    if len(bucket) >= max_requests:
                        retry = max(1, int(window_seconds - (now - bucket[0])))
                        resp = jsonify({
                            'error': 'Too many requests. Please wait a moment and try again.',
                            'retry_after': retry,
                        })
                        resp.headers['Retry-After'] = str(retry)
                        return resp, 429
                    bucket.append(now)
                    _hits[key] = bucket
            except Exception:
                pass  # fail open — never block the API on a limiter fault
            return fn(*args, **kwargs)
        return wrapper
    return decorator
