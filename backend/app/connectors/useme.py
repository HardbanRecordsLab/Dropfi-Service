"""Useme.com — Polish freelance marketplace, public jobs RSS feed (no key).

https://useme.com/pl/rss/jobs/ — one <item> per open project (zlecenie).
"""
from __future__ import annotations

from .base import Connector, NormalizedListing
from ._http import get_text, parse_date, parse_feed, strip_html

FEED = "https://useme.com/pl/rss/jobs/"


class UsemeConnector(Connector):
    slug = "useme"
    name = "Useme"
    kind = "listings"
    region = "PL"
    homepage = "https://useme.com"
    access = "public RSS feed"

    def fetch_listings(self, limit: int) -> list[NormalizedListing]:
        entries = parse_feed(get_text(FEED))
        out: list[NormalizedListing] = []
        for e in entries[:limit]:
            link = e.get("link", "")
            out.append(NormalizedListing(
                external_id=e.get("guid") or link,
                url=link,
                title=e.get("title", "").strip(),
                description=strip_html(e.get("description")),
                category=(e.get("categories") or [""])[0],
                tags=e.get("categories") or [],
                location="Polska / zdalnie",
                is_remote=True,
                language="pl",
                currency="PLN",
                posted_at=parse_date(e.get("published")),
            ))
        return out
