"""Freelancer.com — official REST API (api docs: developers.freelancer.com),
authenticated with a personal Access Token from the account's Developer
settings (accounts.freelancer.com/settings/develop — no OAuth redirect dance
needed, confirmed working directly as a Bearer token). Bid-based project
marketplace — real client project requests, not employment postings.

GET /api/projects/0.1/projects/active is actually public (works with no auth
at all), but the token is sent anyway for the better authenticated rate
limit; confirmed valid against GET /api/users/0.1/self.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.config import settings

from .base import Connector, NormalizedListing
from ._http import get_json

API = "https://www.freelancer.com/api/projects/0.1/projects/active"

# Freelancer.com "job" ids relevant to HRL Digital's services (from
# GET /projects/0.1/jobs — bare "PHP"/"JavaScript" deliberately excluded,
# they're tagged on too many unrelated postings, e.g. trading bots).
JOB_IDS = [17, 69, 77, 120, 137, 335, 502, 759, 788, 1031, 2298, 2376, 2701, 2723]

# Multi-industry pass for the marketplace board: one full-text query per trade,
# so DROPIFY isn't only web/e-commerce work.
INDUSTRY_QUERIES = [
    "accounting", "bookkeeping", "legal", "translation", "copywriting", "data entry",
    "virtual assistant", "customer support", "autocad", "architecture", "engineering",
    "tutoring", "recruitment", "lead generation", "video editing", "photography",
    "voice over", "logo design", "social media marketing", "excel", "research",
    "interior design", "fitness", "music production", "logistics",
]


class FreelancerConnector(Connector):
    slug = "freelancer"
    name = "Freelancer.com"
    kind = "listings"
    region = "global"
    homepage = "https://www.freelancer.com"
    access = "REST API (personal access token)"
    requires_key = True

    def is_enabled(self) -> bool:
        return bool(settings.FREELANCER_ACCESS_TOKEN)

    def _fetch(self, extra: list[tuple], limit: int) -> list[dict]:
        params = [("limit", limit), ("full_description", "true"), ("job_details", "true")] + extra
        data = get_json(
            API,
            params=params,
            headers={"Authorization": f"Bearer {settings.FREELANCER_ACCESS_TOKEN}"},
        )
        return ((data or {}).get("result") or {}).get("projects", [])

    def fetch_listings(self, limit: int) -> list[NormalizedListing]:
        # 1) agency-relevant jobs (HRL Digital sales agent), 2) every other trade.
        # Half the budget for agency work, the rest spread across trades.
        # list(): never extend the object returned by the HTTP layer in place (a cached/shared response doubled 25 times
        # in the tests and exhausted the CI runner's memory)
        projects = list(self._fetch([("jobs[]", job_id) for job_id in JOB_IDS], max(1, limit // 2)))
        per_query = max(1, (limit - limit // 2) // len(INDUSTRY_QUERIES))
        for q in INDUSTRY_QUERIES:
            try:
                projects += self._fetch([("query", q)], per_query)
            except Exception:  # noqa: BLE001 — one failing query must not drop the rest
                continue
        seen, out = set(), []
        for p in projects:
            pid = p.get("id")
            if pid in seen:
                continue
            seen.add(pid)
            out.append(self._normalize(p))
        return out[:limit]

    @staticmethod
    def _normalize(p: dict) -> NormalizedListing:
        budget = p.get("budget") or {}
        currency = (p.get("currency") or {}).get("code", "")
        amount_min = budget.get("minimum")
        amount_max = budget.get("maximum")
        # Amounts stay in the listing's own currency (``currency`` travels with them) and are converted to USD where they
        # are compared (scoring, import). Before 2026-10-27 non-PLN budgets were dropped, so every USD/INR lead looked
        # "budget unknown" and tiny-budget leads were never filtered out.
        budget_min, budget_max = amount_min, amount_max
        sign = (p.get("currency") or {}).get("sign", "")
        budget_text = (
            f"{sign}{amount_min:.0f} - {sign}{amount_max:.0f}"
            if amount_min is not None and amount_max is not None else ""
        )

        jobs = p.get("jobs") or []
        seo_url = p.get("seo_url") or str(p.get("id"))

        return NormalizedListing(
            external_id=str(p.get("id")),
            url=f"https://www.freelancer.com/projects/{seo_url}",
            title=(p.get("title") or "").strip(),
            description=(p.get("description") or p.get("preview_description") or "").strip(),
            budget_min=budget_min,
            budget_max=budget_max,
            budget_text=budget_text,
            currency=currency,
            category=(jobs[0].get("name") if jobs else ""),
            tags=[j.get("name") for j in jobs if j.get("name")],
            is_remote=True,
            language=p.get("language") or "en",
            posted_at=_parse_unix(p.get("time_submitted") or p.get("submitdate")),
        )


def _parse_unix(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None
