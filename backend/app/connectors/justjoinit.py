"""Just Join IT — Polish/EU tech job board, public offers API (no key).

https://api.justjoin.it/v2/user-panel/offers (requires the ``version: 2`` header).
Best-effort: if the endpoint shape changes the scan task logs it per-source.
"""
from __future__ import annotations

from .base import Connector, NormalizedListing
from ._http import get_json, parse_date, strip_html

API = "https://api.justjoin.it/v2/user-panel/offers"


class JustJoinItConnector(Connector):
    slug = "justjoinit"
    name = "Just Join IT"
    kind = "listings"
    region = "PL"
    homepage = "https://justjoin.it"
    access = "public JSON API"

    def fetch_listings(self, limit: int) -> list[NormalizedListing]:
        data = get_json(API, headers={"version": "2"})
        rows = data.get("data", data) if isinstance(data, dict) else data
        out: list[NormalizedListing] = []
        for job in (rows or [])[:limit]:
            slug = job.get("slug", "")
            employment = (job.get("employmentTypes") or [{}])[0]
            salary_from = employment.get("fromPln") or employment.get("from")
            salary_to = employment.get("toPln") or employment.get("to")
            multi = job.get("multilocation") or []
            city = job.get("city") or (multi[0].get("city") if multi else "")
            out.append(NormalizedListing(
                external_id=slug or job.get("id", ""),
                url=f"https://justjoin.it/offers/{slug}" if slug else job.get("url", ""),
                title=job.get("title", "").strip(),
                description=strip_html(job.get("body")),
                company=job.get("companyName", ""),
                budget_min=_num(salary_from),
                budget_max=_num(salary_to),
                currency=employment.get("currency", "PLN") or "PLN",
                category=job.get("categoryId") and str(job.get("categoryId")) or "IT",
                tags=[s.get("name") for s in (job.get("requiredSkills") or []) if isinstance(s, dict) and s.get("name")]
                     or [s for s in (job.get("skills") or []) if isinstance(s, str)],
                location=city or "Polska",
                is_remote=(job.get("workplaceType") == "remote") or bool(job.get("remote")),
                language="pl",
                posted_at=parse_date(job.get("publishedAt")),
            ))
        return out


def _num(v):
    try:
        return float(v) or None
    except (TypeError, ValueError):
        return None
