"""The list of every Portal Radar connector. Import and append to add one."""
from __future__ import annotations

from .adzuna import AdzunaConnector
from .arbeitnow import ArbeitnowConnector
from .base import Connector
from .devto import DevToConnector
from .github import GitHubConnector
from .hn_hiring import HackerNewsHiringConnector
from .jobicy import JobicyConnector
from .justjoinit import JustJoinItConnector
from .remoteok import RemoteOkConnector
from .remotive import RemotiveConnector
from .stackoverflow import StackOverflowConnector
from .usajobs import USAJobsConnector
from .useme import UsemeConnector
from .weworkremotely import WeWorkRemotelyConnector

ALL_CONNECTORS: list[Connector] = [
    # demand side — job / gig leads
    RemotiveConnector(),
    RemoteOkConnector(),
    ArbeitnowConnector(),
    JobicyConnector(),
    WeWorkRemotelyConnector(),
    HackerNewsHiringConnector(),
    UsemeConnector(),
    JustJoinItConnector(),
    AdzunaConnector(),
    USAJobsConnector(),
    # supply side — contractor / specialist profiles
    GitHubConnector(),
    StackOverflowConnector(),
    DevToConnector(),
]

_BY_SLUG = {c.slug: c for c in ALL_CONNECTORS}


def get(slug: str) -> Connector | None:
    return _BY_SLUG.get(slug)


def enabled_connectors() -> list[Connector]:
    return [c for c in ALL_CONNECTORS if c.is_enabled()]
