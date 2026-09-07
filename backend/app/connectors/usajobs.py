"""USAJOBS — U.S. federal government job openings API (free key).

https://developer.usajobs.gov/ — set USAJOBS_API_KEY and USAJOBS_EMAIL to enable.
"""
from __future__ import annotations

from app.config import settings

from .base import Connector, NormalizedListing
from ._http import get_json, parse_date, strip_html

API = "https://data.usajobs.gov/api/search"


class USAJobsConnector(Connector):
    slug = "usajobs"
    name = "USAJOBS"
    kind = "listings"
    region = "US"
    homepage = "https://www.usajobs.gov"
    access = "REST API (free key)"
    requires_key = True

    def is_enabled(self) -> bool:
        return bool(settings.USAJOBS_API_KEY and settings.USAJOBS_EMAIL)

    def fetch_listings(self, limit: int) -> list[NormalizedListing]:
        data = get_json(API, params={"Keyword": "digital services", "ResultsPerPage": min(limit, 50)},
                        headers={
                            "Authorization-Key": settings.USAJOBS_API_KEY,
                            "User-Agent": settings.USAJOBS_EMAIL,
                            "Host": "data.usajobs.gov",
                        })
        out: list[NormalizedListing] = []
        items = (((data or {}).get("SearchResult") or {}).get("SearchResultItems")) or []
        for item in items[:limit]:
            d = item.get("MatchedObjectDescriptor") or {}
            pay = (d.get("PositionRemuneration") or [{}])[0]
            out.append(NormalizedListing(
                external_id=str(item.get("MatchedObjectId")),
                url=d.get("PositionURI", ""),
                title=d.get("PositionTitle", "").strip(),
                description=strip_html((d.get("UserArea") or {}).get("Details", {}).get("JobSummary")
                                       or d.get("QualificationSummary")),
                company=d.get("OrganizationName", ""),
                budget_min=_num(pay.get("MinimumRange")),
                budget_max=_num(pay.get("MaximumRange")),
                currency=pay.get("CurrencyCode", "USD") or "USD",
                location=", ".join(l.get("LocationName", "") for l in (d.get("PositionLocation") or []))[:250],
                posted_at=parse_date(d.get("PublicationStartDate")),
            ))
        return out


def _num(v):
    try:
        return float(v) or None
    except (TypeError, ValueError):
        return None
