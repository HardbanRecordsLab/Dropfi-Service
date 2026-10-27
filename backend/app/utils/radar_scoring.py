"""Scores a Portal Radar lead (ExternalListing) against the HRL Digital
agency profile — how well does this listing fit OUR services, not whether
it's a good job in general. Pure function, no DB/LLM/network calls, so it's
cheap to run on every new listing and trivial to unit test.

Score is 0-100, built from:
  - semantic fit: listing text vs. the agency's services/keywords (embed_text
    + cosine_similarity from app/utils/ai.py — same embedding util the rest
    of the platform already uses for job/freelancer matching, not a new one)
  - keyword overlap bonus (keywords_include hits)
  - budget vs. profile.min_budget_usd
  - listing language vs. profile.languages
  - freshness (posted_at)
A keywords_exclude hit short-circuits to 0 regardless of everything else.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.utils.ai import cosine_similarity, embed_text
from app.utils.currency import to_usd

SEMANTIC_WEIGHT = 55
KEYWORD_WEIGHT = 20
BUDGET_WEIGHT = 15
LANGUAGE_WEIGHT = 5
FRESHNESS_WEIGHT = 5

FRESHNESS_DAYS = 14

# HRL Digital sells project work, not jobs for a person to fill. Full-time-
# employment listings (hiring boards mixed into otherwise-relevant sources)
# otherwise score similarly to real project leads under the weights above,
# so they're explicitly penalized/boosted on top of the weighted total.
_FULL_TIME_SIGNALS = (
    "etat", "umowa o pracę", "umowa o prace", "pełny wymiar", "full-time", "full time",
    "part-time", "part time", "permanent position", "(m/w/d)", "m/w/d", "(f/m/d)", "f/m/d",
    "(m/f)", "(f/m)", "pracownik etatowy", "benefits package", "paid holidays", "pto",
)
_PROJECT_SIGNALS = (
    "zlecenie", "zlecenia", "zleceniodawca", "projekt", "freelance", "freelancer",
    "umowa zlecenie", "umowa o dzieło", "umowa o dzielo", "jednorazowe", "b2b", "kontrakt",
)
FULL_TIME_PENALTY = 20
PROJECT_BONUS = 10
# A lead whose KNOWN budget (top of the range, in USD) is under the agency minimum can still win 70 points on text fit
# alone; cap it below RADAR_ALERT_MIN_SCORE so it is never alerted or offered. Unknown budgets are not capped.
BELOW_MIN_BUDGET_CAP = 25


def _text_of(listing: Any) -> str:
    title = getattr(listing, "title", "") or ""
    description = getattr(listing, "description", "") or ""
    category = getattr(listing, "category", "") or ""
    tags = getattr(listing, "tags", None) or []
    return " ".join([title, description, category, " ".join(str(t) for t in tags)]).lower()


def _profile_text(profile: dict) -> str:
    parts: list[str] = [profile.get("tagline", "")]
    for svc in profile.get("services", []):
        parts.append(str(svc.get("name", "")))
        parts.append(str(svc.get("description", "")))
    parts.extend(str(k) for k in profile.get("keywords_include", []))
    return " ".join(parts)


def _matched_keywords(text: str, keywords: list[str]) -> list[str]:
    return [kw for kw in keywords if kw and str(kw).lower() in text]


def _budget_usd(listing: Any) -> float | None:
    budget = getattr(listing, "budget_max", None) or getattr(listing, "budget_min", None)
    if not budget:
        return None
    return to_usd(float(budget), getattr(listing, "currency", None))


def _budget_component(listing: Any, profile: dict) -> tuple[float, str | None]:
    min_budget = profile.get("min_budget_usd") or 0
    budget = getattr(listing, "budget_max", None) or getattr(listing, "budget_min", None)
    if budget:  # stored in the listing currency (PLN when empty) -> USD, the unit of min_budget_usd
        budget = to_usd(float(budget), getattr(listing, "currency", None))
    if not budget:
        return BUDGET_WEIGHT * 0.5, None  # unknown budget — neutral, not a penalty
    if min_budget and budget < min_budget:
        return 0.0, f"budżet poniżej minimum ({budget:.0f} < {min_budget:.0f} USD)"
    return float(BUDGET_WEIGHT), f"budżet {budget:.0f} USD"


def _language_component(listing: Any, profile: dict) -> tuple[float, str | None]:
    languages = [str(l).lower() for l in profile.get("languages", [])]
    lang = (getattr(listing, "language", "") or "").lower()
    if not languages or not lang:
        return LANGUAGE_WEIGHT * 0.5, None
    if lang in languages:
        return float(LANGUAGE_WEIGHT), None
    return 0.0, f"język ogłoszenia ({lang}) poza obsługiwanymi"


def _freshness_component(listing: Any) -> float:
    posted_at = getattr(listing, "posted_at", None)
    if not posted_at:
        return FRESHNESS_WEIGHT * 0.5
    now = datetime.now(timezone.utc)
    posted = posted_at if posted_at.tzinfo else posted_at.replace(tzinfo=timezone.utc)
    age_days = (now - posted).total_seconds() / 86400
    return float(FRESHNESS_WEIGHT) if age_days <= FRESHNESS_DAYS else 0.0


def score_listing(listing: Any, profile: dict) -> tuple[int, str]:
    """Returns (fit_score 0-100, fit_reason — one Polish sentence)."""
    text = _text_of(listing)

    exclude = [k for k in profile.get("keywords_exclude", []) if k]
    hit_exclude = _matched_keywords(text, exclude)
    if hit_exclude:
        return 0, f"Wykluczone: pasuje do słowa kluczowego z listy wykluczeń ({hit_exclude[0]})."

    profile_text = _profile_text(profile)
    semantic = cosine_similarity(embed_text(text), embed_text(profile_text))
    semantic_points = semantic * SEMANTIC_WEIGHT

    include = [k for k in profile.get("keywords_include", []) if k]
    matched = _matched_keywords(text, include)
    keyword_points = min(len(matched), 4) / 4 * KEYWORD_WEIGHT if include else KEYWORD_WEIGHT * 0.5

    budget_points, budget_note = _budget_component(listing, profile)
    language_points, language_note = _language_component(listing, profile)
    freshness_points = _freshness_component(listing)

    total = semantic_points + keyword_points + budget_points + language_points + freshness_points

    is_full_time = any(sig in text for sig in _FULL_TIME_SIGNALS)
    is_project = any(sig in text for sig in _PROJECT_SIGNALS)
    if is_full_time:
        total -= FULL_TIME_PENALTY
    if is_project:
        total += PROJECT_BONUS
    score = int(round(max(0.0, min(100.0, total))))

    min_budget = profile.get("min_budget_usd") or 0
    budget_usd = _budget_usd(listing)
    below_min = bool(min_budget and budget_usd and budget_usd < min_budget)
    if below_min:
        score = min(score, BELOW_MIN_BUDGET_CAP)

    category = getattr(listing, "category", "") or "brak kategorii"
    budget_text = getattr(listing, "budget_text", "") or budget_note or "budżet nieznany"
    reason_parts = [category, budget_text]
    if matched:
        reason_parts.append("pasuje: " + ", ".join(matched[:3]))
    if language_note:
        reason_parts.append(language_note)
    if below_min:
        reason_parts.append(f"budżet poniżej minimum agencji ({budget_usd:.0f} < {min_budget:.0f} USD) — wynik ograniczony")
    if is_full_time:
        reason_parts.append("sygnały pracy na etat (obniżono wynik)")
    if is_project:
        reason_parts.append("sygnały zlecenia/projektu (podwyższono wynik)")
    fit_reason = ", ".join(str(p) for p in reason_parts if p) + "."

    return score, fit_reason
