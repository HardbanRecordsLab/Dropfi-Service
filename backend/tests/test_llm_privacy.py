"""LLM calls must ask OpenRouter for providers that do not store/train on prompts."""
from types import SimpleNamespace

from app.config import settings
from app.utils import llm


class _FakeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="OK"))])


def _fake_client():
    completions = _FakeCompletions()
    return SimpleNamespace(chat=SimpleNamespace(completions=completions)), completions


def test_openrouter_requests_deny_data_collection(monkeypatch):
    client, completions = _fake_client()
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "LLM_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setattr(settings, "LLM_DATA_COLLECTION", "deny")
    monkeypatch.setattr(llm, "_get_client", lambda: client)

    assert llm.llm_text("hello") == "OK"
    assert completions.calls[0]["extra_body"] == {"provider": {"data_collection": "deny"}}


def test_non_openrouter_base_url_sends_no_provider_preference(monkeypatch):
    client, completions = _fake_client()
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "LLM_BASE_URL", "http://localhost:8000/v1")
    monkeypatch.setattr(settings, "LLM_DATA_COLLECTION", "deny")
    monkeypatch.setattr(llm, "_get_client", lambda: client)

    assert llm.llm_text("hello") == "OK"
    assert "extra_body" not in completions.calls[0]


def test_empty_setting_sends_no_provider_preference(monkeypatch):
    client, completions = _fake_client()
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "LLM_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setattr(settings, "LLM_DATA_COLLECTION", "")
    monkeypatch.setattr(llm, "_get_client", lambda: client)

    assert llm.llm_text("hello") == "OK"
    assert "extra_body" not in completions.calls[0]
