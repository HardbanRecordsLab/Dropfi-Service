"""Portal Radar: what the portal itself says about a lead — is it still open, how crowded is it, is it a repost.

A lead that scores well on paper is worthless when the project is already awarded or has hundreds of bids, or when the
same client posted it four times with slightly different titles. These helpers are pure (no DB) except ``fetch_market``,
which asks the portal's official API (same tokens the connectors already use) about ONE project.
"""
from __future__ import annotations

import re

from app.config import settings

# bids above these counts make a win unlikely for a small agency
CROWDED_BIDS = 100
VERY_CROWDED_BIDS = 200
CROWDED_PENALTY = 15
VERY_CROWDED_PENALTY = 25

_CLOSED_WORDS = re.compile(r"(chosen|suspend|closed|cancel|complet|archiv|expire|selected|awarded|frozen|rejected|finish)", re.I)
_STOP = {"the", "and", "for", "with", "need", "needed", "want", "looking", "build", "create", "website", "web", "app",
         "oraz", "dla", "szukam", "potrzebuję", "potrzebuje", "jest", "nie"}


def title_tokens(title: str) -> frozenset[str]:
    words = re.findall(r"[a-ząćęłńóśźż0-9]{3,}", (title or "").lower())
    return frozenset(w for w in words if w not in _STOP)


def similar_titles(a: str, b: str, threshold: float = 0.5) -> bool:
    """Jaccard similarity of significant title words (reposts of one job usually share its distinctive nouns)."""
    ta, tb = title_tokens(a), title_tokens(b)
    if len(ta) < 2 or len(tb) < 2:
        return False
    return len(ta & tb) / len(ta | tb) >= threshold


def find_duplicate_ids(leads: list[tuple[str, str, float]]) -> dict[str, str]:
    """``leads`` = [(id, title, fit_score)] of ONE source, recent only. Returns {duplicate_id: kept_id}.
    The best-scoring lead of each near-identical group is kept, the others are reposts."""
    ordered = sorted(leads, key=lambda r: (-(r[2] or 0), r[0]))
    kept: list[tuple[str, str]] = []
    dups: dict[str, str] = {}
    for lead_id, title, _ in ordered:
        match = next((k_id for k_id, k_title in kept if similar_titles(title, k_title)), None)
        if match:
            dups[lead_id] = match
        else:
            kept.append((lead_id, title))
    return dups


def market_adjustment(market: dict | None) -> tuple[int, str | None, bool]:
    """(score delta, Polish note, closed). ``market`` = {"open": bool, "status": str, "bids": int|None}."""
    if not market:
        return 0, None, False
    if market.get("open") is False:
        return 0, f"zamknięte w portalu ({market.get('status') or 'brak statusu'})", True
    bids = market.get("bids")
    if isinstance(bids, (int, float)):
        if bids >= VERY_CROWDED_BIDS:
            return -VERY_CROWDED_PENALTY, f"{int(bids)} ofert — bardzo duża konkurencja", False
        if bids >= CROWDED_BIDS:
            return -CROWDED_PENALTY, f"{int(bids)} ofert — duża konkurencja", False
    return 0, None, False


def _status_is_open(source: str, status: str) -> bool:
    status = (status or "").strip()
    if source == "freelancer":
        return status.lower() == "active"
    return not _CLOSED_WORDS.search(status)          # freelancehunt: anything that is not chosen/suspended/closed counts as open


def fetch_market(source: str, external_id: str) -> dict | None:
    """Ask the portal about one project. None when the source is unsupported or the call fails (never raises)."""
    from app.connectors._http import get_json
    try:
        if source == "freelancer" and settings.FREELANCER_ACCESS_TOKEN:
            data = get_json(f"https://www.freelancer.com/api/projects/0.1/projects/{external_id}/",
                            params={"compact": "true", "bid_stats": "true"},
                            headers={"Authorization": f"Bearer {settings.FREELANCER_ACCESS_TOKEN}"})
            result = (data or {}).get("result") or {}
            status = str(result.get("status") or "")
            return {"open": _status_is_open(source, status), "status": status,
                    "bids": (result.get("bid_stats") or {}).get("bid_count")}
        if source == "freelancehunt" and settings.FREELANCEHUNT_API_TOKEN:
            data = get_json(f"https://api.freelancehunt.com/v2/projects/{external_id}",
                            headers={"Authorization": f"Bearer {settings.FREELANCEHUNT_API_TOKEN}"})
            attrs = ((data or {}).get("data") or {}).get("attributes") or {}
            status = str((attrs.get("status") or {}).get("name") or "")
            return {"open": _status_is_open(source, status), "status": status, "bids": attrs.get("bid_count")}
    except Exception:  # noqa: BLE001 — a failing portal call must not stop the refresh of the other leads
        return None
    return None
