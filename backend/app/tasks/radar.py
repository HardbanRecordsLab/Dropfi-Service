"""Portal Radar: periodic scan of external job portals.

Pulls job leads (demand) and contractor profiles (supply) from every enabled
connector in ``app.connectors.registry`` using official APIs / RSS only, and
upserts them into ``external_listings`` / ``external_talent`` (deduplicated on
``(source, external_id)``). One connector raising never aborts the run — each
failure is recorded on its own ``RadarScanLog`` row.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy.orm import Session

from app.config import settings
from app.connectors import registry
from app.connectors.base import Connector, NormalizedListing, NormalizedTalent
from app.database import SessionLocal
from app.models import ExternalListing, ExternalTalent, RadarScanLog

logger = logging.getLogger(__name__)


def _upsert_listing(db: Session, source: str, item: NormalizedListing) -> bool:
    row = (db.query(ExternalListing)
           .filter(ExternalListing.source == source,
                   ExternalListing.external_id == item.external_id)
           .first())
    is_new = row is None
    if is_new:
        row = ExternalListing(source=source, external_id=item.external_id, status="new")
        db.add(row)
    # A fetch is authoritative for the content fields; status / imported_job_id
    # are DROPIFY-side workflow state and are never touched here.
    row.url = item.url
    row.title = (item.title or "")[:500]
    row.description = item.description or ""
    row.company = item.company or ""
    row.budget_min = item.budget_min
    row.budget_max = item.budget_max
    row.budget_text = item.budget_text or ""
    row.currency = item.currency or ""
    row.category = item.category or ""
    row.tags = list(item.tags or [])
    row.location = item.location or ""
    row.is_remote = bool(item.is_remote)
    row.language = item.language or "en"
    row.contact = item.contact or ""
    row.posted_at = item.posted_at
    row.fetched_at = datetime.now(timezone.utc)
    row.raw = item.raw or {}
    return is_new


def _upsert_talent(db: Session, source: str, item: NormalizedTalent) -> bool:
    row = (db.query(ExternalTalent)
           .filter(ExternalTalent.source == source,
                   ExternalTalent.external_id == item.external_id)
           .first())
    is_new = row is None
    if is_new:
        row = ExternalTalent(source=source, external_id=item.external_id, status="new")
        db.add(row)
    row.url = item.url
    row.name = (item.name or "")[:255]
    row.headline = item.headline or ""
    row.skills = list(item.skills or [])
    row.location = item.location or ""
    row.country = item.country or ""
    row.rate_text = item.rate_text or ""
    row.rating = item.rating
    row.followers = item.followers
    row.portfolio_url = item.portfolio_url or ""
    row.avatar_url = item.avatar_url or ""
    row.fetched_at = datetime.now(timezone.utc)
    row.raw = item.raw or {}
    return is_new


def run_scan(connector: Connector, db: Session) -> RadarScanLog:
    """Scan one connector and write its RadarScanLog row. Never raises."""
    log = RadarScanLog(source=connector.slug)
    db.add(log)
    db.commit()

    limit = settings.RADAR_MAX_PER_SOURCE
    try:
        if connector.kind in ("listings", "both"):
            listings = connector.fetch_listings(limit) or []
            log.listings_found = len(listings)
            for item in listings:
                if not item.external_id or not item.url:
                    continue
                if _upsert_listing(db, connector.slug, item):
                    log.listings_new += 1

        if connector.kind in ("talent", "both"):
            talent = connector.fetch_talent(limit) or []
            log.talents_found = len(talent)
            for item in talent:
                if not item.external_id or not item.url:
                    continue
                if _upsert_talent(db, connector.slug, item):
                    log.talents_new += 1

        log.ok = True
    except Exception as exc:  # noqa: BLE001 — isolate every source
        db.rollback()
        db.add(log)
        log.ok = False
        log.error = f"{type(exc).__name__}: {exc}"[:2000]
        logger.warning("Portal Radar: source %s failed — %s", connector.slug, exc)

    log.finished_at = datetime.now(timezone.utc)
    db.commit()
    return log


@shared_task(name="app.tasks.radar.scan_source")
def scan_source(slug: str) -> dict:
    connector = registry.get(slug)
    if connector is None:
        return {"error": f"unknown source: {slug}"}
    db = SessionLocal()
    try:
        log = run_scan(connector, db)
        return {"source": slug, "ok": log.ok, "listings_new": log.listings_new,
                "talents_new": log.talents_new, "error": log.error}
    finally:
        db.close()


@shared_task(name="app.tasks.radar.scan_all_sources")
def scan_all_sources() -> dict:
    if not settings.RADAR_ENABLED:
        return {"skipped": "RADAR_ENABLED is false"}
    db = SessionLocal()
    results = []
    try:
        for connector in registry.enabled_connectors():
            log = run_scan(connector, db)
            results.append({"source": connector.slug, "ok": log.ok,
                            "listings_new": log.listings_new, "talents_new": log.talents_new})
    finally:
        db.close()
    return {"scanned": len(results), "results": results}
