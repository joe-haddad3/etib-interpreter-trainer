"""
LLM provider abstraction.

Module code should call generate_text() instead of binding directly to a
specific cloud or local model client. This keeps Groq usable while allowing
Aya Expanse 8B to run locally after the model files are downloaded.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from groq import Groq

from config import (
    GROQ_API_KEY,
    LLM_PROVIDER,
    LOCAL_MODEL_DEVICE_MAP,
    LOCAL_MODEL_ID,
    LOCAL_MODEL_PATH,
    LOCAL_MODEL_TORCH_DTYPE,
    PRIMARY_LLM_MODEL,
)

_groq_client: Groq | None = None
_local_pipeline: Any | None = None
_local_tokenizer: Any | None = None


def generate_text(
    messages: list[dict[str, str]],
    max_tokens: int = 1800,
    temperature: float = 0.7,
) -> str:
    """Generate text using the configured provider."""
    provider = LLM_PROVIDER.lower().strip()

    if provider == 'local_aya':
        return _generate_with_local_aya(messages, max_tokens, temperature)

    if provider == 'groq':
        return _generate_with_groq(messages, max_tokens, temperature)

    raise RuntimeError(
        f"Unsupported LLM_PROVIDER '{LLM_PROVIDER}'. Use 'groq' or 'local_aya'."
    )


def _generate_with_groq(
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> str:
    global _groq_client

    if not GROQ_API_KEY:
        raise RuntimeError('GROQ_API_KEY is not configured')

    if _groq_client is None:
        _groq_client = Groq(api_key=GROQ_API_KEY)

    response = _groq_client.chat.completions.create(
        model=PRIMARY_LLM_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


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


def _load_local_aya() -> tuple[Any, Any]:
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    except ImportError as exc:
        raise RuntimeError(
            'Local Aya requires torch, transformers, accelerate, sentencepiece, '
            'and huggingface-hub. Install them with: '
            'pip install torch transformers accelerate sentencepiece huggingface-hub'
        ) from exc

    model_ref = LOCAL_MODEL_PATH or LOCAL_MODEL_ID
    if LOCAL_MODEL_PATH and not Path(LOCAL_MODEL_PATH).exists():
        raise RuntimeError(
            f"LOCAL_MODEL_PATH does not exist: {LOCAL_MODEL_PATH}. "
            'Download Aya Expanse 8B manually and point LOCAL_MODEL_PATH '
            'to the downloaded model folder.'
        )

    tokenizer = AutoTokenizer.from_pretrained(model_ref, trust_remote_code=True)
    model_kwargs: dict[str, Any] = {
        'device_map': LOCAL_MODEL_DEVICE_MAP,
        'trust_remote_code': True,
    }

    if LOCAL_MODEL_TORCH_DTYPE == 'auto':
        model_kwargs['torch_dtype'] = 'auto'
    elif hasattr(torch, LOCAL_MODEL_TORCH_DTYPE):
        model_kwargs['torch_dtype'] = getattr(torch, LOCAL_MODEL_TORCH_DTYPE)

    model = AutoModelForCausalLM.from_pretrained(model_ref, **model_kwargs)
    generator = pipeline('text-generation', model=model, tokenizer=tokenizer)
    return generator, tokenizer


def _messages_to_prompt(messages: list[dict[str, str]], tokenizer: Any) -> str:
    if hasattr(tokenizer, 'apply_chat_template') and tokenizer.chat_template:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    parts = []
    for message in messages:
        role = message.get('role', 'user').upper()
        content = message.get('content', '')
        parts.append(f'{role}:\n{content}')
    parts.append('ASSISTANT:\n')
    return '\n\n'.join(parts)
