"""Adzuna — global job aggregator API (free tier, requires an app id + key).

https://developer.adzuna.com/ — set ADZUNA_APP_ID / ADZUNA_APP_KEY to enable.
Covers ~20 countries incl. PL, GB, US, DE.
"""
from __future__ import annotations

from app.config import settings

from .base import Connector, NormalizedListing
from ._http import get_json, parse_date, strip_html

API = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"
COUNTRIES = ["pl", "gb", "us", "de"]


class AdzunaConnector(Connector):
    slug = "adzuna"
    name = "Adzuna"
    kind = "listings"
    region = "global"
    homepage = "https://www.adzuna.com"
    access = "REST API (free key)"
    requires_key = True

    def is_enabled(self) -> bool:
        return bool(settings.ADZUNA_APP_ID and settings.ADZUNA_APP_KEY)

    def fetch_listings(self, limit: int) -> list[NormalizedListing]:
        per_country = max(1, limit // len(COUNTRIES))
        out: list[NormalizedListing] = []
        for country in COUNTRIES:
            data = get_json(API.format(country=country), params={
                "app_id": settings.ADZUNA_APP_ID,
                "app_key": settings.ADZUNA_APP_KEY,
                "results_per_page": per_country,
                "what_or": "ecommerce shopify freelance developer designer copywriter",
                "content-type": "application/json",
            })
            for job in (data or {}).get("results", []):
                out.append(NormalizedListing(
                    external_id=str(job.get("id")),
                    url=job.get("redirect_url", ""),
                    title=job.get("title", "").strip(),
                    description=strip_html(job.get("description")),
                    company=(job.get("company") or {}).get("display_name", ""),
                    budget_min=job.get("salary_min"),
                    budget_max=job.get("salary_max"),
                    currency={"pl": "PLN", "gb": "GBP", "us": "USD", "de": "EUR"}[country],
                    category=(job.get("category") or {}).get("label", ""),
                    location=(job.get("location") or {}).get("display_name", ""),
                    language="pl" if country == "pl" else "en",
                    posted_at=parse_date(job.get("created")),
                ))
                if len(out) >= limit:
                    return out
        return out
