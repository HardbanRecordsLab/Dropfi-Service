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

    def fetch_listings(self, limit: int) -> list[NormalizedListing]:
        params = [
            ("limit", limit),
            ("full_description", "true"),
            ("job_details", "true"),
        ]
        params += [("jobs[]", job_id) for job_id in JOB_IDS]

        data = get_json(
            API,
            params=params,
            headers={"Authorization": f"Bearer {settings.FREELANCER_ACCESS_TOKEN}"},
        )
        projects = ((data or {}).get("result") or {}).get("projects", [])
        return [self._normalize(p) for p in projects[:limit]]

    @staticmethod
    def _normalize(p: dict) -> NormalizedListing:
        budget = p.get("budget") or {}
        currency = (p.get("currency") or {}).get("code", "")
        amount_min = budget.get("minimum")
        amount_max = budget.get("maximum")
        # Scoring compares budget_max against a PLN threshold with no
        # currency conversion — most Freelancer.com budgets are USD, so only
        # pass them through when they're actually PLN, else budget_text-only.
        if currency == "PLN":
            budget_min, budget_max = amount_min, amount_max
        else:
            budget_min, budget_max = None, None
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
