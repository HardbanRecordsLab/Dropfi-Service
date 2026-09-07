"""GitHub — contractor discovery via the public Search API (supply side).

https://api.github.com/search/users — works with no auth (low rate limit);
set ``GITHUB_TOKEN`` to raise it. Legitimate recruiting use of a public API.
"""
from __future__ import annotations

from app.config import settings

from .base import Connector, NormalizedTalent
from ._http import get_json

SEARCH = "https://api.github.com/search/users"
USER = "https://api.github.com/users/"

# Broad, e-commerce / digital-services flavoured talent queries.
QUERIES = [
    "shopify developer",
    "e-commerce frontend",
    "react developer freelance",
    "python automation",
    "product photographer",  # matches bios/orgs; noisy but harmless
]


class GitHubConnector(Connector):
    slug = "github"
    name = "GitHub"
    kind = "talent"
    region = "global"
    homepage = "https://github.com"
    access = "public Search API (token optional)"
    requires_key = False

    def _headers(self) -> dict:
        h = {"Accept": "application/vnd.github+json"}
        if settings.GITHUB_TOKEN:
            h["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
        return h

    def fetch_talent(self, limit: int) -> list[NormalizedTalent]:
        per_query = max(1, limit // len(QUERIES))
        out: list[NormalizedTalent] = []
        seen: set[str] = set()
        for q in QUERIES:
            data = get_json(SEARCH, params={"q": f"{q} type:user", "per_page": per_query},
                            headers=self._headers())
            for item in (data or {}).get("items", []):
                login = item.get("login")
                if not login or login in seen:
                    continue
                seen.add(login)
                profile = {}
                try:
                    profile = get_json(USER + login, headers=self._headers()) or {}
                except Exception:  # noqa: BLE001 — enrichment is best-effort
                    profile = {}
                out.append(NormalizedTalent(
                    external_id=str(item.get("id") or login),
                    url=item.get("html_url", f"https://github.com/{login}"),
                    name=profile.get("name") or login,
                    headline=(profile.get("bio") or q).strip()[:480],
                    skills=[q],
                    location=profile.get("location", "") or "",
                    followers=profile.get("followers"),
                    portfolio_url=profile.get("blog", "") or "",
                    avatar_url=item.get("avatar_url", ""),
                    raw={"login": login, "public_repos": profile.get("public_repos"), "query": q},
                ))
                if len(out) >= limit:
                    return out
        return out
