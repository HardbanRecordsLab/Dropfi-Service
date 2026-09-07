"""Arbeitnow — https://www.arbeitnow.com/api/job-board-api (public JSON, no key).

EU-heavy job board; free, CORS-open, explicitly offered for aggregation.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .base import Connector, NormalizedListing
from ._http import get_json, strip_html

API = "https://www.arbeitnow.com/api/job-board-api"


class ArbeitnowConnector(Connector):
    slug = "arbeitnow"
    name = "Arbeitnow"
    kind = "listings"
    region = "EU"
    homepage = "https://www.arbeitnow.com"
    access = "public JSON API"

    def fetch_listings(self, limit: int) -> list[NormalizedListing]:
        data = get_json(API)
        out: list[NormalizedListing] = []
        for job in (data or {}).get("data", [])[:limit]:
            created = job.get("created_at")
            posted = None
            if isinstance(created, (int, float)):
                posted = datetime.fromtimestamp(created, tz=timezone.utc)
            out.append(NormalizedListing(
                external_id=job.get("slug", ""),
                url=job.get("url", ""),
                title=job.get("title", "").strip(),
                description=strip_html(job.get("description")),
                company=job.get("company_name", ""),
                tags=[t for t in (job.get("tags") or []) if t],
                location=job.get("location", ""),
                is_remote=bool(job.get("remote")),
                language="de" if "Berlin" in (job.get("location") or "") else "en",
                posted_at=posted,
                raw={"job_types": job.get("job_types")},
            ))
        return out
