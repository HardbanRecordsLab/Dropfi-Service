"""Shared HTTP + feed-parsing helpers for connectors.

Deliberately dependency-free beyond ``httpx`` (already a project dep): RSS/Atom
is parsed with the stdlib ``xml.etree`` so Portal Radar adds no new packages.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

import httpx

from app.config import settings

USER_AGENT = (
    "DropifyPortalRadar/1.0 (+https://dropify.app; contact "
    f"{settings.SUPPORT_EMAIL}) job-aggregator"
)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\r\f\v]+")


def get_json(url: str, *, params: dict | None = None, headers: dict | None = None) -> object:
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        h.update(headers)
    resp = httpx.get(url, params=params, headers=h, timeout=settings.RADAR_HTTP_TIMEOUT,
                     follow_redirects=True)
    resp.raise_for_status()
    return resp.json()


def get_text(url: str, *, params: dict | None = None, headers: dict | None = None) -> str:
    h = {"User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    resp = httpx.get(url, params=params, headers=h, timeout=settings.RADAR_HTTP_TIMEOUT,
                     follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def strip_html(value: str | None, *, limit: int = 4000) -> str:
    if not value:
        return ""
    text = _TAG_RE.sub(" ", value)
    text = (text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " "))
    text = _WS_RE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:limit]


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        dt = parsedate_to_datetime(value)          # RFC-822 (RSS)
        if dt is not None:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_feed(xml_text: str) -> list[dict]:
    """Return a list of ``{title, link, description, published, guid, categories}``
    dicts from an RSS 2.0 or Atom feed."""
    root = ET.fromstring(xml_text.encode("utf-8") if isinstance(xml_text, str) else xml_text)
    items: list[dict] = []

    # RSS: <rss><channel><item>...   Atom: <feed><entry>...
    nodes = [el for el in root.iter() if _localname(el.tag) in ("item", "entry")]
    for node in nodes:
        entry: dict = {"categories": []}
        for child in node:
            name = _localname(child.tag)
            if name == "title":
                entry["title"] = (child.text or "").strip()
            elif name == "link":
                href = child.attrib.get("href")
                entry["link"] = (href or child.text or "").strip()
            elif name in ("description", "summary", "content"):
                entry.setdefault("description", (child.text or "").strip())
            elif name in ("pubDate", "published", "updated"):
                entry.setdefault("published", (child.text or "").strip())
            elif name in ("guid", "id"):
                entry["guid"] = (child.text or "").strip()
            elif name == "category":
                term = child.attrib.get("term") or (child.text or "")
                if term.strip():
                    entry["categories"].append(term.strip())
        if entry.get("title") or entry.get("link"):
            items.append(entry)
    return items
