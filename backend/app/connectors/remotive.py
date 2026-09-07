"""Remotive — https://remotive.com/api/remote-jobs (public JSON, no key)."""
from __future__ import annotations

from .base import Connector, NormalizedListing
from ._http import get_json, parse_date, strip_html

API = "https://remotive.com/api/remote-jobs"


class RemotiveConnector(Connector):
    slug = "remotive"
    name = "Remotive"
    kind = "listings"
    region = "global"
    homepage = "https://remotive.com"
    access = "public JSON API"

    def fetch_listings(self, limit: int) -> list[NormalizedListing]:
        data = get_json(API, params={"limit": limit})
        out: list[NormalizedListing] = []
        for job in (data or {}).get("jobs", [])[:limit]:
            out.append(NormalizedListing(
                external_id=str(job.get("id")),
                url=job.get("url", ""),
                title=job.get("title", "").strip(),
                description=strip_html(job.get("description")),
                company=job.get("company_name", ""),
                budget_text=job.get("salary", "") or "",
                category=job.get("category", ""),
                tags=[t for t in (job.get("tags") or []) if t],
                location=job.get("candidate_required_location", "") or "Remote",
                is_remote=True,
                posted_at=parse_date(job.get("publication_date")),
                raw={"job_type": job.get("job_type")},
            ))
        return out
