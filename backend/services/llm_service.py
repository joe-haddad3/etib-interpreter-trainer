"""
LLM provider abstraction.

Module code should call generate_text() instead of binding directly to a
specific cloud or local model client.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from config import (
    GOOGLE_AI_KEY,
    GROQ_API_KEY,
    LLM_PROVIDER,
    LOCAL_MODEL_DEVICE_MAP,
    LOCAL_MODEL_ID,
    LOCAL_MODEL_PATH,
    LOCAL_MODEL_TORCH_DTYPE,
    PRIMARY_LLM_MODEL,
    REMOTE_AYA_TIMEOUT_SECONDS,
    REMOTE_AYA_URL,
    REMOTE_AYA_VERIFY_SSL,
)

# All clients are lazy — nothing is imported or created until first call.
_local_pipeline: Any | None = None
_local_tokenizer: Any | None = None


def _active_groq_key() -> str | None:
    """Return the per-request user key, falling back to the server default key."""
    try:
        from flask import g
        key = getattr(g, 'groq_api_key', None)
        if key:
            return key
    except RuntimeError:
        pass
    return GROQ_API_KEY or None

# gemini-3.5-flash-lite, NOT gemini-3.5-flash: the regular flash model has a
# punishing free-tier cap of only 20 requests/DAY, and it burns its whole output
# budget on hidden "thinking" (needs thinkingBudget:0). The -lite model has a far
# larger free-tier daily allowance (~1000/day) AND doesn't think by default, so
# speeches come back full-length with no workaround. Overridable via env.
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')


def generate_text(
    messages: list[dict[str, str]],
    max_tokens: int = 1800,
    temperature: float = 0.7,
) -> str:
    """Generate text using the configured provider."""
    provider = LLM_PROVIDER.lower().strip()

    if provider == 'gemini':
        return _generate_with_gemini(messages, max_tokens, temperature)

    if provider == 'groq':
        return _generate_with_groq(messages, max_tokens, temperature)

    if provider == 'local_aya':
        return _generate_with_local_aya(messages, max_tokens, temperature)

    if provider == 'remote_aya':
        return _generate_with_remote_aya(messages, max_tokens, temperature)

    raise RuntimeError(
        f"Unsupported LLM_PROVIDER '{LLM_PROVIDER}'. Use 'gemini', 'groq', 'local_aya', or 'remote_aya'."
    )


# ── Gemini — raw REST (no SDK, no httpx conflicts) ───────────────────────────

def _gemini_retry_delay(resp: Any, attempt: int) -> float:
    """Seconds to wait before retrying a 429/503. Honours the API's suggested
    retryDelay / Retry-After when present, capped at 15s so a request can't hang."""
    # Retry-After header (seconds)
    header = (resp.headers.get('Retry-After') or '').strip()
    if header.isdigit():
        return min(15.0, float(header))
    # RetryInfo.retryDelay in the JSON error body, e.g. "7s"
    try:
        for detail in resp.json().get('error', {}).get('details', []) or []:
            delay = str(detail.get('retryDelay', '')).rstrip('s')
            if delay.replace('.', '', 1).isdigit():
                return min(15.0, float(delay))
    except Exception:
        pass
    return min(15.0, 5.0 * (attempt + 1))  # 5s, then 10s


def _generate_with_gemini(
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> str:
    """Call Gemini via the REST API using requests — no google-genai SDK needed."""
    import os
    key = os.getenv('GOOGLE_AI_KEY', '').strip()
    if not key or key == 'your_google_ai_key_here':
        raise RuntimeError(
            'GOOGLE_AI_KEY is not configured. '
            'Get a free key at https://aistudio.google.com and add it to backend/.env'
        )

    import requests

    system_text = ''
    user_text = ''
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role == 'system':
            system_text = content
        elif role == 'user':
            user_text = content

    # Prepend system instruction directly into the user turn — works on all API versions
    combined = f"{system_text}\n\n{user_text}".strip() if system_text else user_text

    gen_config: dict[str, Any] = {
        'maxOutputTokens': max_tokens,
        'temperature': temperature,
    }
    # The full (non-lite) flash models are REASONING models: they spend the whole
    # maxOutputTokens budget on hidden "thinking" and return truncated/empty text
    # unless thinkingBudget:0 disables it. The -lite models DON'T think by default
    # and REJECT this field (400), so only send it for a non-lite model.
    if 'lite' not in GEMINI_MODEL and 'latest' not in GEMINI_MODEL:
        gen_config['thinkingConfig'] = {'thinkingBudget': 0}

    payload: dict[str, Any] = {
        'contents': [{'role': 'user', 'parts': [{'text': combined}]}],
        'generationConfig': gen_config,
    }

    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/'
        f'{GEMINI_MODEL}:generateContent?key={key}'
    )

    # The free tier caps REQUESTS PER MINUTE. A burst of big speeches (a marathon
    # is several calls) can briefly 429 / 503 even though there is plenty of daily
    # quota left. Wait out the short window and retry so the user never sees it.
    import time
    resp = None
    for attempt in range(3):
        resp = requests.post(url, json=payload, timeout=120)
        if resp.ok:
            break
        if resp.status_code in (429, 503) and attempt < 2:
            time.sleep(_gemini_retry_delay(resp, attempt))
            continue
        raise RuntimeError(f'Gemini API error {resp.status_code}: {resp.text[:400]}')

    data = resp.json()
    try:
        candidate = data['candidates'][0]
        parts = candidate.get('content', {}).get('parts', []) or []
        text = ''.join(p.get('text', '') for p in parts).strip()
        if text:
            return text
        # Empty content — usually finishReason MAX_TOKENS with the whole budget
        # eaten by thinking. Surfaced clearly so it never silently truncates.
        raise RuntimeError(
            f"Gemini returned no text (finishReason="
            f"{candidate.get('finishReason')}); raise maxOutputTokens or check thinkingConfig."
        )
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f'Unexpected Gemini response shape: {data}') from exc


# ── Groq ─────────────────────────────────────────────────────────────────────

def _generate_with_groq(
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> str:
    global _groq_client

    key = _active_groq_key()
    if not key:
        raise RuntimeError(
            'No Groq API key found. Please open Settings and add your '
            'personal Groq API key (free at console.groq.com).'
        )

    from groq import Groq
    from config import groq_extra_params
    client = Groq(api_key=key)

    response = client.chat.completions.create(
        model=PRIMARY_LLM_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        **groq_extra_params(PRIMARY_LLM_MODEL),
    )
    return (response.choices[0].message.content or '').strip()


# ── Local Aya ─────────────────────────────────────────────────────────────────

def _generate_with_local_aya(
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> str:
    global _local_pipeline, _local_tokenizer

    if _local_pipeline is None or _local_tokenizer is None:
        _local_pipeline, _local_tokenizer = _load_local_aya()

    prompt = _messages_to_prompt(messages, _local_tokenizer)
    outputs = _local_pipeline(
        prompt,
        max_new_tokens=max_tokens,
        do_sample=temperature > 0,
        temperature=temperature,
        return_full_text=False,
    )
    return outputs[0]['generated_text'].strip()


# ── Remote Aya ────────────────────────────────────────────────────────────────

def _generate_with_remote_aya(
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> str:
    if not REMOTE_AYA_URL:
        raise RuntimeError('REMOTE_AYA_URL is not configured.')

    import requests

    response = requests.post(
        REMOTE_AYA_URL,
        headers={'ngrok-skip-browser-warning': 'true'},
        json={'messages': messages, 'max_tokens': max_tokens, 'temperature': temperature},
        timeout=REMOTE_AYA_TIMEOUT_SECONDS,
        verify=REMOTE_AYA_VERIFY_SSL,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        body = response.text.strip()[:500]
        raise RuntimeError(
            f'remote_aya HTTP {response.status_code}: {body or "<empty>"}'
        ) from exc

    data = response.json()
    text = data.get('text')
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError('remote_aya returned an empty or invalid response')
    return text.strip()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_local_aya() -> tuple[Any, Any]:
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    except ImportError as exc:
        raise RuntimeError(
            'Local Aya requires torch, transformers, accelerate, sentencepiece, '
            'and huggingface-hub.'
        ) from exc

    model_ref = LOCAL_MODEL_PATH or LOCAL_MODEL_ID
    if LOCAL_MODEL_PATH and not Path(LOCAL_MODEL_PATH).exists():
        raise RuntimeError(f'LOCAL_MODEL_PATH does not exist: {LOCAL_MODEL_PATH}')

    tokenizer = AutoTokenizer.from_pretrained(model_ref, trust_remote_code=True)
    model_kwargs: dict[str, Any] = {
        'device_map': LOCAL_MODEL_DEVICE_MAP,
        'trust_remote_code': True,
    }
    if LOCAL_MODEL_TORCH_DTYPE == 'auto':
        model_kwargs['torch_dtype'] = 'auto'
    elif hasattr(__import__('torch'), LOCAL_MODEL_TORCH_DTYPE):
        model_kwargs['torch_dtype'] = getattr(__import__('torch'), LOCAL_MODEL_TORCH_DTYPE)

    model = AutoModelForCausalLM.from_pretrained(model_ref, **model_kwargs)
    return pipeline('text-generation', model=model, tokenizer=tokenizer), tokenizer


def _messages_to_prompt(messages: list[dict[str, str]], tokenizer: Any) -> str:
    if hasattr(tokenizer, 'apply_chat_template') and tokenizer.chat_template:
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )
    parts = []
    for message in messages:
        role = message.get('role', 'user').upper()
        content = message.get('content', '')
        parts.append(f'{role}:\n{content}')
    parts.append('ASSISTANT:\n')
    return '\n\n'.join(parts)
