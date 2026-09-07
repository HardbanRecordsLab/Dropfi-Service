"""RemoteOK — https://remoteok.com/api (public JSON, no key).

The first array element is a legal/metadata object and is skipped.
"""
from __future__ import annotations

from .base import Connector, NormalizedListing
from ._http import get_json, parse_date, strip_html

API = "https://remoteok.com/api"


def _num(v):
    try:
        return float(v) or None
    except (TypeError, ValueError):
        return None


class RemoteOkConnector(Connector):
    slug = "remoteok"
    name = "RemoteOK"
    kind = "listings"
    region = "global"
    homepage = "https://remoteok.com"
    access = "public JSON API"

    def fetch_listings(self, limit: int) -> list[NormalizedListing]:
        data = get_json(API)
        out: list[NormalizedListing] = []
        for job in (data or []):
            if not isinstance(job, dict) or not job.get("id"):
                continue  # skip the leading legal-notice element
            out.append(NormalizedListing(
                external_id=str(job.get("id")),
                url=job.get("url") or job.get("apply_url", ""),
                title=(job.get("position") or job.get("title") or "").strip(),
                description=strip_html(job.get("description")),
                company=job.get("company", ""),
                budget_min=_num(job.get("salary_min")),
                budget_max=_num(job.get("salary_max")),
                currency="USD" if job.get("salary_min") else "",
                tags=[t for t in (job.get("tags") or []) if t],
                location=job.get("location", "") or "Remote",
                is_remote=True,
                posted_at=parse_date(job.get("date")),
            ))
            if len(out) >= limit:
                break
        return out
