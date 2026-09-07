"""Base types for Portal Radar connectors."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

ConnectorKind = Literal["listings", "talent", "both"]


@dataclass
class NormalizedListing:
    """A job/gig lead, normalised across every source."""
    external_id: str
    url: str
    title: str
    description: str = ""
    company: str = ""
    budget_min: float | None = None
    budget_max: float | None = None
    budget_text: str = ""
    currency: str = ""
    category: str = ""
    tags: list[str] = field(default_factory=list)
    location: str = ""
    is_remote: bool = False
    language: str = "en"
    contact: str = ""
    posted_at: datetime | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class NormalizedTalent:
    """A contractor/specialist profile, normalised across every source."""
    external_id: str
    url: str
    name: str
    headline: str = ""
    skills: list[str] = field(default_factory=list)
    location: str = ""
    country: str = ""
    rate_text: str = ""
    rating: float | None = None
    followers: int | None = None
    portfolio_url: str = ""
    avatar_url: str = ""
    raw: dict = field(default_factory=dict)


class Connector:
    """Subclass this, set the class attributes, override the ``fetch_*``
    method(s) that apply. Every method must be defensive: return whatever it
    parsed and let exceptions bubble to the scan task, which logs them per
    source so one broken portal never aborts the whole run."""

    slug: str = ""
    name: str = ""
    kind: ConnectorKind = "listings"
    region: str = "global"           # "global" | "PL" | "EU" | "US" | ...
    homepage: str = ""
    requires_key: bool = False
    access: str = "public API"       # short human note shown in the UI

    def is_enabled(self) -> bool:
        return True

    def fetch_listings(self, limit: int) -> list[NormalizedListing]:
        return []

    def fetch_talent(self, limit: int) -> list[NormalizedTalent]:
        return []
