"""Portal Radar: periodic scan of external job portals.

Pulls job leads (demand) and contractor profiles (supply) from every enabled
connector in ``app.connectors.registry`` using official APIs / RSS only, and
upserts them into ``external_listings`` / ``external_talent`` (deduplicated on
``(source, external_id)``). One connector raising never aborts the run — each
failure is recorded on its own ``RadarScanLog`` row.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

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
        result = {"source": slug, "ok": log.ok, "listings_new": log.listings_new,
                  "talents_new": log.talents_new, "error": log.error}
    finally:
        db.close()
    _trigger_scoring()
    return result


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
    _trigger_scoring()
    return {"scanned": len(results), "results": results}


def _trigger_scoring() -> None:
    """Fire score_and_alert_new_listings after a scan. A failure here — broker
    down, scoring error, n8n unreachable — must never make the scan itself
    look like it failed, so every path is swallowed and logged."""
    try:
        score_and_alert_new_listings.delay()
    except Exception:  # noqa: BLE001 — broker down -> run inline
        try:
            score_and_alert_new_listings()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Portal Radar: score_and_alert_new_listings failed — %s", exc)


@shared_task(name="app.tasks.radar.score_and_alert_new_listings")
def score_and_alert_new_listings() -> dict:
    """HRL Digital sales agent: scores every listing with ``fit_score IS NULL``
    against the agency profile (``app/utils/agency_profile.py``); for any
    listing scoring >= ``RADAR_ALERT_MIN_SCORE`` drafts an offer (up to
    ``RADAR_AUTO_OFFER_MAX`` per run, skipping ones that already have a draft)
    and sends exactly one Telegram alert via n8n, deduped on ``alerted_at``.
    Never sends an offer itself — I always copy/send it by hand.
    """
    from app.utils.agency_profile import load_agency_profile
    from app.utils.ai import generate_offer
    from app.utils.n8n import notify_n8n
    from app.utils.radar_scoring import score_listing

    db = SessionLocal()
    scored = alerted = offers_generated = 0
    try:
        profile = load_agency_profile()

        unscored = db.query(ExternalListing).filter(ExternalListing.fit_score.is_(None)).all()
        for row in unscored:
            score, reason = score_listing(row, profile)
            row.fit_score = float(score)
            row.fit_reason = reason
            scored += 1
        db.commit()

        if profile.get("is_template"):
            return {"scored": scored, "alerted": 0, "offers_generated": 0,
                    "skipped": "agency_profile.json is still the template"}

        to_alert = (
            db.query(ExternalListing)
            .filter(ExternalListing.fit_score >= settings.RADAR_ALERT_MIN_SCORE,
                    ExternalListing.alerted_at.is_(None))
            .order_by(ExternalListing.fit_score.desc())
            .limit(settings.RADAR_AUTO_OFFER_MAX)
            .all()
        )
        for row in to_alert:
            try:
                if not row.offer_text:
                    offer = generate_offer(row, profile)
                    row.offer_text = offer["offer_text"]
                    row.offer_language = offer["offer_language"]
                    row.offer_price_min = offer["price_min"]
                    row.offer_price_max = offer["price_max"]
                    row.offer_questions = offer["questions"]
                    row.offer_generated_at = datetime.now(timezone.utc)
                    offers_generated += 1
                row.alerted_at = datetime.now(timezone.utc)
                db.commit()

                notify_n8n("radar-lead", {
                    "id": row.id,
                    "title": row.title,
                    "source": row.source,
                    "url": row.url,
                    "budget_text": row.budget_text,
                    "fit_score": row.fit_score,
                    "fit_reason": row.fit_reason,
                    "offer_text": (row.offer_text or "")[:1500],
                    "dashboard_url": f"{settings.FRONTEND_URL}/dashboard/radar?listing={row.id}",
                })
                alerted += 1
            except Exception as exc:  # noqa: BLE001 — one bad listing must not stop the rest
                db.rollback()
                logger.warning("Portal Radar: alert failed for listing %s — %s", row.id, exc)
    finally:
        db.close()
    return {"scored": scored, "alerted": alerted, "offers_generated": offers_generated}


REFRESH_MIN_FIT = 30
REFRESH_WINDOW_DAYS = 21
REFRESH_RECHECK_HOURS = 20
REPOST_CAP = 20


@shared_task(name="app.tasks.radar.refresh_lead_market")
def refresh_lead_market(max_checks: int = 60) -> dict:
    """Keeps the sales agent honest: for the best-scoring recent leads asks the portal whether the project is still
    open and how many bids it has, and flags near-identical reposts of one job.

    Idempotent — the score the lead had before any adjustment is remembered in ``raw["market"]["base_score"]``, so
    running it again never stacks penalties. Closed leads get fit_score 0 and are dismissed; crowded ones lose points;
    reposts are capped below the alert threshold. Never touches leads already worked on (pipeline set) or imported."""
    from app.utils.radar_market import fetch_market, find_duplicate_ids, market_adjustment

    db = SessionLocal()
    checked = closed = crowded = reposts = 0
    try:
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=REFRESH_WINDOW_DAYS)
        rows = (db.query(ExternalListing)
                .filter(ExternalListing.fit_score >= REFRESH_MIN_FIT, ExternalListing.status == "new",
                        ExternalListing.pipeline.is_(None), ExternalListing.fetched_at >= since)
                .order_by(ExternalListing.fit_score.desc()).limit(400).all())

        def base_of(row) -> float:
            return float((row.raw or {}).get("market", {}).get("base_score", row.fit_score))

        # 1) reposts: within one source keep the best-scoring lead of each near-identical group
        by_source: dict[str, list] = {}
        for row in rows:
            by_source.setdefault(row.source, []).append(row)
        by_id = {r.id: r for r in rows}
        for source_rows in by_source.values():
            dups = find_duplicate_ids([(r.id, r.title or "", base_of(r)) for r in source_rows])
            for dup_id, kept_id in dups.items():
                row = by_id[dup_id]
                market = dict((row.raw or {}).get("market", {}))
                if market.get("dup_of"):
                    continue
                market.setdefault("base_score", row.fit_score)
                market["dup_of"] = kept_id
                row.raw = {**(row.raw or {}), "market": market}
                row.fit_score = float(min(row.fit_score, REPOST_CAP))
                row.fit_reason = f"Powtórzone ogłoszenie (to samo zlecenie co {kept_id}). " + (row.fit_reason or "")
                reposts += 1
        db.commit()

        # 2) portal status + bid count for the best leads not checked in the last day
        stale_before = now - timedelta(hours=REFRESH_RECHECK_HOURS)
        for row in rows:
            if checked >= max_checks:
                break
            if row.source not in ("freelancer", "freelancehunt") or (row.raw or {}).get("market", {}).get("dup_of"):
                continue
            market = dict((row.raw or {}).get("market", {}))
            last = market.get("checked_at")
            if last and datetime.fromisoformat(last) > stale_before:
                continue
            info = fetch_market(row.source, row.external_id)
            if info is None:
                continue
            checked += 1
            market.setdefault("base_score", row.fit_score)
            market.update(info, checked_at=now.isoformat())
            delta, note, is_closed = market_adjustment(info)
            row.raw = {**(row.raw or {}), "market": market}
            if is_closed:
                row.fit_score = 0.0
                row.fit_reason = f"Zamknięte w portalu: {info.get('status') or 'brak statusu'}. " + (row.fit_reason or "")
                row.status = "dismissed"
                closed += 1
            else:
                row.fit_score = float(max(0.0, market["base_score"] + delta))
                if note:
                    row.fit_reason = f"{note.capitalize()}. " + (row.fit_reason or "")
                    crowded += 1
            row.updated_at = now
        db.commit()
    finally:
        db.close()
    result = {"checked": checked, "closed": closed, "crowded": crowded, "reposts": reposts}
    logger.info("Radar refresh: %s", result)
    return result


@shared_task(name="app.tasks.radar.keep_min_open_jobs")
def keep_min_open_jobs() -> dict:
    """Close stale imported leads, then import fresh ones until RADAR_MIN_OPEN_JOBS are open."""
    if not settings.RADAR_ENABLED or settings.RADAR_MIN_OPEN_JOBS <= 0:
        return {"skipped": True}
    from app.utils.radar_import import expire_stale_imports, top_up_open_jobs
    db = SessionLocal()
    try:
        closed = expire_stale_imports(db)
        result = top_up_open_jobs(db)
        result["closed_stale"] = closed
        logger.info("Radar top-up: %s", result)
        return result
    finally:
        db.close()
