"""Jobicy — https://jobicy.com/api/v2/remote-jobs (public JSON, no key)."""
from __future__ import annotations

from .base import Connector, NormalizedListing
from ._http import get_json, parse_date, strip_html

API = "https://jobicy.com/api/v2/remote-jobs"


class JobicyConnector(Connector):
    slug = "jobicy"
    name = "Jobicy"
    kind = "listings"
    region = "global"
    homepage = "https://jobicy.com"
    access = "public JSON API"

    def fetch_listings(self, limit: int) -> list[NormalizedListing]:
        data = get_json(API, params={"count": min(limit, 50)})
        out: list[NormalizedListing] = []
        for job in (data or {}).get("jobs", [])[:limit]:
            out.append(NormalizedListing(
                external_id=str(job.get("id")),
                url=job.get("url", ""),
                title=job.get("jobTitle", "").strip(),
                description=strip_html(job.get("jobExcerpt") or job.get("jobDescription")),
                company=job.get("companyName", ""),
                budget_min=_num(job.get("annualSalaryMin")),
                budget_max=_num(job.get("annualSalaryMax")),
                currency=job.get("salaryCurrency", "") or "",
                category=(job.get("jobIndustry") or [""])[0] if isinstance(job.get("jobIndustry"), list) else (job.get("jobIndustry") or ""),
                tags=job.get("jobType") if isinstance(job.get("jobType"), list) else [],
                location=job.get("jobGeo", "") or "Anywhere",
                is_remote=True,
                posted_at=parse_date(job.get("pubDate")),
            ))
        return out


def _num(v):
    try:
        return float(v) or None
    except (TypeError, ValueError):
        return None
