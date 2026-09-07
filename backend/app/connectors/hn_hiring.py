"""Hacker News "Ask HN: Who is hiring?" — via the public Algolia HN Search API.

http://hn.algolia.com/api/v1 — no key. Each top-level comment in the monthly
thread is one hiring lead, usually with a contact email in the text.
"""
from __future__ import annotations

import re

from .base import Connector, NormalizedListing
from ._http import get_json, parse_date, strip_html

SEARCH = "http://hn.algolia.com/api/v1/search"
ITEMS = "http://hn.algolia.com/api/v1/search_by_date"

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_REMOTE_RE = re.compile(r"\bREMOTE\b", re.IGNORECASE)


class HackerNewsHiringConnector(Connector):
    slug = "hn_hiring"
    name = "Hacker News — Who is hiring"
    kind = "listings"
    region = "global"
    homepage = "https://news.ycombinator.com"
    access = "public Algolia API"

    def _latest_thread_id(self) -> str | None:
        data = get_json(SEARCH, params={
            "query": "Ask HN: Who is hiring?",
            "tags": "story,author_whoishiring",
            "hitsPerPage": 1,
        })
        hits = (data or {}).get("hits") or []
        return hits[0].get("objectID") if hits else None

    def fetch_listings(self, limit: int) -> list[NormalizedListing]:
        thread_id = self._latest_thread_id()
        if not thread_id:
            return []
        data = get_json(ITEMS, params={
            "tags": f"comment,story_{thread_id}",
            "hitsPerPage": min(limit, 100),
        })
        out: list[NormalizedListing] = []
        for hit in (data or {}).get("hits", []):
            text = strip_html(hit.get("comment_text"))
            if not text or len(text) < 40:
                continue
            first_line = text.splitlines()[0][:200]
            emails = _EMAIL_RE.findall(text)
            out.append(NormalizedListing(
                external_id=str(hit.get("objectID")),
                url=f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                title=first_line,
                description=text,
                company=first_line.split("|")[0].strip()[:120],
                tags=["who-is-hiring"],
                location="Remote" if _REMOTE_RE.search(text) else "",
                is_remote=bool(_REMOTE_RE.search(text)),
                contact=emails[0] if emails else "",
                posted_at=parse_date(hit.get("created_at")),
                raw={"author": hit.get("author"), "thread_id": thread_id},
            ))
            if len(out) >= limit:
                break
        return out
