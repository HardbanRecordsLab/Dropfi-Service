"""WP Zlecenia — Polish WordPress freelance job board, public WordPress RSS
feed (no key, no login wall). Exactly the category of lead HRL Digital wants:
real client project requests (not full-time job postings), WordPress-specific.

https://wpzlecenia.pl/feed/ — standard WordPress post feed, category "Zlecenia".
"""
from __future__ import annotations

from .base import Connector, NormalizedListing
from ._http import get_text, parse_date, parse_feed, strip_html

FEED = "https://wpzlecenia.pl/feed/"


class WpZleceniaConnector(Connector):
    slug = "wpzlecenia"
    name = "WP Zlecenia"
    kind = "listings"
    region = "PL"
    homepage = "https://wpzlecenia.pl"
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
                category="WordPress",
                tags=["wordpress"] + (e.get("categories") or []),
                location="Polska / zdalnie",
                is_remote=True,
                language="pl",
                currency="PLN",
                posted_at=parse_date(e.get("published")),
            ))
        return out
