"""Freelancehunt — Ukrainian/CIS freelance project marketplace, official
REST API (JSON:API style, personal access token, self-service — no approval
wait). https://apidocs.freelancehunt.com/ — get a token at
https://freelancehunt.com/my/api and set FREELANCEHUNT_API_TOKEN.

Real client project requests (bid-based), not employment postings — the
right category of lead for HRL Digital. Verified against the live API:
listings include things like "Перенос сайта на вордпрес" (move a site to
WordPress) and PrestaShop/e-commerce fixes.
"""
from __future__ import annotations

import re
from datetime import datetime

from app.config import settings

from .base import Connector, NormalizedListing
from ._http import get_json, strip_html

API_BASE = "https://api.freelancehunt.com/v2"

# Skill ids relevant to HRL Digital's services (from GET /skills — no
# "WordPress" id exists; CMS work falls under "Content Management Systems").
# PHP, Web Design, Website Maintenance, Online Stores & E-commerce,
# Content Management Systems, Website Development, Web Programming, HTML & CSS.
SKILL_IDS = "1,43,45,68,78,96,99,124"

_CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")


def _guess_language(text: str) -> str:
    """Accept-Language only affects skill-name translation, not the employer's
    own text, so listings are a mix of Ukrainian/Russian and English/Polish."""
    if not text:
        return "en"
    cyrillic = len(_CYRILLIC_RE.findall(text))
    return "uk" if cyrillic > len(text) * 0.15 else "en"


class FreelancehuntConnector(Connector):
    slug = "freelancehunt"
    name = "Freelancehunt"
    kind = "listings"
    region = "global"
    homepage = "https://freelancehunt.com"
    access = "REST API (personal token)"
    requires_key = True

    def is_enabled(self) -> bool:
        return bool(settings.FREELANCEHUNT_API_TOKEN)

    def fetch_listings(self, limit: int) -> list[NormalizedListing]:
        headers = {
            "Authorization": f"Bearer {settings.FREELANCEHUNT_API_TOKEN}",
            "Accept-Language": "en",
        }
        out: list[NormalizedListing] = []
        page = 1
        max_pages = max(1, (limit // 10) + 1)
        while len(out) < limit and page <= max_pages:
            data = get_json(
                f"{API_BASE}/projects",
                params={"filter[skill_id]": SKILL_IDS, "page[number]": page},
                headers=headers,
            )
            items = (data or {}).get("data", [])
            if not items:
                break
            for item in items:
                out.append(self._normalize(item))
                if len(out) >= limit:
                    break
            page += 1
        return out

    @staticmethod
    def _normalize(item: dict) -> NormalizedListing:
        attrs = item.get("attributes", {})
        budget = attrs.get("budget") or {}
        employer = attrs.get("employer") or {}
        skills = attrs.get("skills") or []
        tags = attrs.get("tags") or []
        links = item.get("links") or {}
        web_url = ((links.get("self") or {}).get("web")
                   or f"https://freelancehunt.com/project/{item.get('id')}.html")

        title = attrs.get("name", "") or ""
        description = strip_html(attrs.get("description") or "")
        currency = budget.get("currency", "")
        amount = budget.get("amount")
        # Scoring compares budget_max against a PLN threshold with no currency
        # conversion — only pass through an amount when it's actually PLN,
        # otherwise a UAH figure would be silently misread as PLN.
        budget_min = amount if currency == "PLN" else None
        budget_max = amount if currency == "PLN" else None
        budget_text = f"{amount} {currency}" if amount else ""

        return NormalizedListing(
            external_id=str(item.get("id")),
            url=web_url,
            title=title.strip(),
            description=description,
            company=" ".join(filter(None, [employer.get("first_name"), employer.get("last_name")]))
                     or employer.get("login", ""),
            budget_min=budget_min,
            budget_max=budget_max,
            budget_text=budget_text,
            currency=currency,
            category=(skills[0].get("name") if skills else ""),
            tags=[s.get("name") for s in skills if s.get("name")]
                 + [t.get("name") for t in tags if t.get("name")],
            is_remote=True,
            language=_guess_language(f"{title} {description}"),
            posted_at=_parse_dt(attrs.get("published_at")),
        )


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
