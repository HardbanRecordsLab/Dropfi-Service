"""Loads the HRL Digital agency profile used by the Portal Radar sales agent
to score leads and draft offers (see app/utils/radar_scoring.py, app/utils/ai.py).

``agency_profile.json`` is real business data — gitignored, never committed.
Falls back to ``agency_profile.example.json`` (committed, all-TODO placeholder
values) so the app still boots with nothing configured; callers must check
``is_template`` and refuse to send real offers/alerts off template data.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_EXAMPLE_PATH = _BACKEND_ROOT / "app" / "data" / "agency_profile.example.json"

_REQUIRED_STRING_FIELDS = ("agency_name", "tagline", "tone", "signature")
_TODO_MARKER = "TODO"

_cache: dict[str, Any] | None = None


def _resolve_path() -> Path:
    p = Path(settings.AGENCY_PROFILE_PATH)
    return p if p.is_absolute() else _BACKEND_ROOT / p


def _looks_like_template(data: dict) -> bool:
    for field in _REQUIRED_STRING_FIELDS:
        value = data.get(field, "")
        if not value or _TODO_MARKER in str(value):
            return True
    if not data.get("services"):
        return True
    for svc in data.get("services", []):
        if _TODO_MARKER in str(svc.get("name", "")) or _TODO_MARKER in str(svc.get("description", "")):
            return True
    return False


def load_agency_profile(*, force_reload: bool = False) -> dict[str, Any]:
    """Returns the agency profile dict plus an ``is_template`` flag.

    Load order: real ``AGENCY_PROFILE_PATH`` first, then the committed
    example as a fallback so the app never fails to boot. Either way the
    returned dict carries ``is_template`` so callers (offer generation,
    alerts) can refuse to act on placeholder data.
    """
    global _cache
    if _cache is not None and not force_reload:
        return _cache

    real_path = _resolve_path()
    path = real_path if real_path.exists() else _EXAMPLE_PATH
    if path is _EXAMPLE_PATH:
        logger.warning(
            "agency_profile.json not found at %s — using the committed example "
            "template (is_template=True). Real offers/alerts are blocked until "
            "a real profile is in place.", real_path,
        )

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:  # noqa: BLE001 — corrupt file must not crash the app
        logger.error("Failed to load agency profile from %s: %s", path, exc)
        with open(_EXAMPLE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        path = _EXAMPLE_PATH

    data.setdefault("services", [])
    data.setdefault("keywords_include", [])
    data.setdefault("keywords_exclude", [])
    data.setdefault("portfolio", [])
    data.setdefault("languages", ["pl", "en"])
    data.setdefault("min_budget_pln", 0)

    data["is_template"] = path is _EXAMPLE_PATH or _looks_like_template(data)
    _cache = data
    return data
