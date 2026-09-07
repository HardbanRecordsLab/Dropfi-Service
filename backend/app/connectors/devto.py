"""DEV Community (dev.to) — article authors by tag, via the public API (no key).

https://dev.to/api/articles?tag=... — each article carries its author; a good
supply-side signal for writers and developers active in a niche.
"""
from __future__ import annotations

from .base import Connector, NormalizedTalent
from ._http import get_json

API = "https://dev.to/api/articles"
TAGS = ["ecommerce", "shopify", "webdev", "productivity", "automation"]


class DevToConnector(Connector):
    slug = "devto"
    name = "DEV Community"
    kind = "talent"
    region = "global"
    homepage = "https://dev.to"
    access = "public JSON API"

    def fetch_talent(self, limit: int) -> list[NormalizedTalent]:
        per_tag = max(1, limit // len(TAGS))
        out: list[NormalizedTalent] = []
        seen: set[str] = set()
        for tag in TAGS:
            data = get_json(API, params={"tag": tag, "per_page": per_tag})
            for art in (data or []):
                user = art.get("user") or {}
                username = user.get("username")
                if not username or username in seen:
                    continue
                seen.add(username)
                out.append(NormalizedTalent(
                    external_id=username,
                    url=f"https://dev.to/{username}",
                    name=user.get("name") or username,
                    headline=(art.get("title") or f"Writes about {tag}")[:480],
                    skills=[tag] + [t for t in (art.get("tag_list") or []) if t][:4],
                    portfolio_url=user.get("website_url", "") or "",
                    avatar_url=user.get("profile_image_90", ""),
                    raw={"latest_article": art.get("url"), "tag": tag},
                ))
                if len(out) >= limit:
                    return out
        return out
