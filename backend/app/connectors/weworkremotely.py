"""We Work Remotely — public RSS feed (no key).

https://weworkremotely.com/remote-jobs.rss
"""
from __future__ import annotations

from .base import Connector, NormalizedListing
from ._http import get_text, parse_date, parse_feed, strip_html

FEED = "https://weworkremotely.com/remote-jobs.rss"


class WeWorkRemotelyConnector(Connector):
    slug = "weworkremotely"
    name = "We Work Remotely"
    kind = "listings"
    region = "global"
    homepage = "https://weworkremotely.com"
    access = "public RSS feed"

    def fetch_listings(self, limit: int) -> list[NormalizedListing]:
        entries = parse_feed(get_text(FEED))
        out: list[NormalizedListing] = []
        for e in entries[:limit]:
            link = e.get("link", "")
            title = e.get("title", "")
            company, _, role = title.partition(":")
            out.append(NormalizedListing(
                external_id=e.get("guid") or link,
                url=link,
                title=title.strip(),
                description=strip_html(e.get("description")),
                company=company.strip() if role else "",
                category=(e.get("categories") or [""])[0],
                tags=e.get("categories") or [],
                location="Remote",
                is_remote=True,
                posted_at=parse_date(e.get("published")),
            ))
        return out
