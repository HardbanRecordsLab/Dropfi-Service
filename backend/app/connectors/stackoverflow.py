"""Stack Overflow — top answerers by tag, via the public Stack Exchange API.

https://api.stackexchange.com/2.3/tags/{tag}/top-answerers/all_time (no key;
keyless quota is small but enough for a periodic scan).
"""
from __future__ import annotations

from .base import Connector, NormalizedTalent
from ._http import get_json

API = "https://api.stackexchange.com/2.3/tags/{tag}/top-answerers/all_time"
TAGS = ["shopify", "woocommerce", "e-commerce", "web-scraping", "automation"]


class StackOverflowConnector(Connector):
    slug = "stackoverflow"
    name = "Stack Overflow"
    kind = "talent"
    region = "global"
    homepage = "https://stackoverflow.com"
    access = "public Stack Exchange API"

    def fetch_talent(self, limit: int) -> list[NormalizedTalent]:
        per_tag = max(1, limit // len(TAGS))
        out: list[NormalizedTalent] = []
        seen: set[str] = set()
        for tag in TAGS:
            data = get_json(API.format(tag=tag), params={
                "site": "stackoverflow", "pagesize": per_tag,
            })
            for row in (data or {}).get("items", []):
                user = row.get("user") or {}
                uid = str(user.get("user_id") or "")
                if not uid or uid in seen:
                    continue
                seen.add(uid)
                out.append(NormalizedTalent(
                    external_id=uid,
                    url=user.get("link", f"https://stackoverflow.com/users/{uid}"),
                    name=user.get("display_name", f"user{uid}"),
                    headline=f"Top {tag} answerer on Stack Overflow",
                    skills=[tag],
                    rating=float(row.get("score")) if row.get("score") is not None else None,
                    followers=user.get("reputation"),
                    avatar_url=user.get("profile_image", ""),
                    raw={"tag": tag, "post_count": row.get("post_count")},
                ))
                if len(out) >= limit:
                    return out
        return out
