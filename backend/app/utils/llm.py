"""Single provider-agnostic LLM entry point.

Everything that used to call Anthropic directly now goes through ``llm_text``.
It speaks the OpenAI-compatible Chat Completions API, so it works with
OpenRouter (default), Groq, DeepSeek, Together, a local vLLM, etc. — only
``LLM_BASE_URL`` / ``OPENROUTER_API_KEY`` / ``LLM_MODEL`` change.

No key configured -> ``llm_enabled()`` is False and every caller falls back to
its rule-based path, exactly like the old ``ANTHROPIC_API_KEY`` guard.
"""
from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger(__name__)

_client = None


def llm_enabled() -> bool:
    return bool(settings.OPENROUTER_API_KEY)


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.LLM_BASE_URL,
            timeout=settings.LLM_TIMEOUT,
            default_headers={
                # OpenRouter attribution headers (ignored by other providers)
                "HTTP-Referer": settings.LLM_APP_URL,
                "X-Title": settings.LLM_APP_NAME,
            },
        )
    return _client


def llm_text(
    prompt: str,
    *,
    system: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.3,
    force_json: bool = False,
) -> str | None:
    """Return the model's text answer, or ``None`` on any failure / no key.

    Tries ``LLM_MODEL`` first, then ``LLM_MODEL_FALLBACK`` on error. Callers
    must treat ``None`` as "use the rule-based fallback".
    """
    if not llm_enabled():
        return None

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    cap = min(max_tokens or settings.LLM_MAX_TOKENS, settings.LLM_MAX_TOKENS)
    kwargs = {"messages": messages, "max_tokens": cap, "temperature": temperature}
    if force_json:
        kwargs["response_format"] = {"type": "json_object"}

    client = _get_client()
    models = [settings.LLM_MODEL]
    if settings.LLM_MODEL_FALLBACK and settings.LLM_MODEL_FALLBACK != settings.LLM_MODEL:
        models.append(settings.LLM_MODEL_FALLBACK)

    for model in models:
        try:
            resp = client.chat.completions.create(model=model, **kwargs)
            text = (resp.choices[0].message.content or "").strip()
            if text:
                return text
            logger.warning("LLM %s returned empty content", model)
        except Exception as exc:  # noqa: BLE001 — any provider error -> try next / fallback
            logger.warning("LLM call failed on %s (%s)", model, exc)
    return None
