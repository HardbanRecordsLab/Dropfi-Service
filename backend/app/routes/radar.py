"""Portal Radar API — browse external job-portal leads (demand) and contractor
profiles (supply) gathered by ``app.connectors`` via official APIs / RSS, and
import a lead as a real DROPIFY job that runs through AI matching.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.connectors import registry
from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import ExternalListing, ExternalTalent, RadarScanLog, User
from app.schemas import ExternalListingOut, ExternalTalentOut, PipelineUpdate, RadarSourceOut
from app.utils.agency_profile import load_agency_profile
from app.utils.ai import generate_offer

router = APIRouter(prefix="/radar", tags=["Portal Radar"])
logger = logging.getLogger(__name__)

_TALENT_STATUSES = {"new", "contacted", "invited", "dismissed"}
_PIPELINE_STATUSES = {"applied", "replied", "won", "lost"}


def _radar_bot(db: Session) -> User:
    """The client account that owns jobs imported from external leads."""
    from app.utils.radar_import import radar_bot
    return radar_bot(db)


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

@router.get("/sources", response_model=list[RadarSourceOut])
def list_sources(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    listing_counts = dict(
        db.query(ExternalListing.source, func.count(ExternalListing.id))
        .group_by(ExternalListing.source).all()
    )
    talent_counts = dict(
        db.query(ExternalTalent.source, func.count(ExternalTalent.id))
        .group_by(ExternalTalent.source).all()
    )
    out = []
    for c in registry.ALL_CONNECTORS:
        last = (db.query(RadarScanLog)
                .filter(RadarScanLog.source == c.slug)
                .order_by(RadarScanLog.started_at.desc())
                .first())
        out.append(RadarSourceOut(
            slug=c.slug, name=c.name, kind=c.kind, region=c.region,
            homepage=c.homepage, access=c.access, requires_key=c.requires_key,
            enabled=registry.is_enabled(c),
            last_scan_at=last.started_at if last else None,
            last_scan_ok=last.ok if last else None,
            last_scan_error=last.error if last else None,
            listings_count=listing_counts.get(c.slug, 0),
            talents_count=talent_counts.get(c.slug, 0),
        ))
    return out


@router.post("/scan")
def trigger_scan(
    source: str = Query("", description="connector slug; empty = all enabled sources"),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    from app.tasks.radar import scan_all_sources, scan_source

    if source:
        if registry.get(source) is None:
            raise HTTPException(status_code=404, detail=f"Unknown source: {source}")
        try:
            scan_source.delay(source)
            return {"status": "queued", "source": source}
        except Exception:  # noqa: BLE001 — Celery/broker down -> run inline
            return {"status": "done", "result": scan_source(source)}

    try:
        scan_all_sources.delay()
        return {"status": "queued", "source": "all"}
    except Exception:  # noqa: BLE001
        return {"status": "done", "result": scan_all_sources()}


# ---------------------------------------------------------------------------
# Listings (demand side)
# ---------------------------------------------------------------------------

@router.get("/listings", response_model=list[ExternalListingOut])
def list_listings(
    source: str = "",
    category: str = "",
    status: str = "",
    remote: bool | None = None,
    q: str = "",
    min_score: float | None = Query(None, description="only listings with fit_score >= this"),
    pipeline: str = Query("", description="applied | replied | won | lost"),
    sort: str = Query("", description="'score' sorts by fit_score desc; default sorts by fetched_at desc"),
    skip: int = 0,
    limit: int = Query(50, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ExternalListing)
    if source:
        query = query.filter(ExternalListing.source == source)
    if category:
        query = query.filter(ExternalListing.category.ilike(f"%{category}%"))
    if status:
        query = query.filter(ExternalListing.status == status)
    if remote is not None:
        query = query.filter(ExternalListing.is_remote == remote)
    if q:
        like = f"%{q}%"
        query = query.filter(ExternalListing.title.ilike(like) | ExternalListing.description.ilike(like))
    if min_score is not None:
        query = query.filter(ExternalListing.fit_score >= min_score)
    if pipeline:
        query = query.filter(ExternalListing.pipeline == pipeline)

    if sort == "score":
        # NULL fit_score (not yet scored) sorts after everything scored, highest first.
        order = (ExternalListing.fit_score.is_(None), ExternalListing.fit_score.desc())
    else:
        order = (ExternalListing.fetched_at.desc(),)
    return (query.order_by(*order)
            .offset(skip).limit(limit).all())


@router.post("/listings/{listing_id}/import")
def import_listing(
    listing_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in ("client", "admin"):
        raise HTTPException(status_code=403, detail="Only clients or admins can import leads")
    row = db.get(ExternalListing, listing_id)
    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")
    if row.status == "imported" and row.imported_job_id:
        raise HTTPException(status_code=409, detail="Already imported")

    from app.utils.radar_import import import_listing_row
    job = import_listing_row(db, row, _radar_bot(db))
    return {"status": "imported", "job_id": job.id}


@router.post("/top-up")
def top_up(
    target: int = Query(None, ge=1, le=2000, description="minimum open jobs (default RADAR_MIN_OPEN_JOBS)"),
    max_age_days: int = Query(None, ge=1, le=90),
    min_fit: float = Query(0, ge=0, le=100),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Admin: import fresh leads until at least `target` jobs are open on the board."""
    from app.utils.radar_import import top_up_open_jobs
    return top_up_open_jobs(db, target=target, max_age_days=max_age_days, min_fit=min_fit)


@router.post("/listings/{listing_id}/offer", response_model=ExternalListingOut)
def generate_listing_offer(
    listing_id: str,
    regenerate: bool = Query(False, description="regenerate even if an offer already exists"),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    row = db.get(ExternalListing, listing_id)
    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")
    if row.offer_text and not regenerate:
        return row

    profile = load_agency_profile()
    if profile.get("is_template"):
        raise HTTPException(
            status_code=409,
            detail="The agency profile (agency_profile.json) is not filled in yet — fill in the "
                   "HRL Digital details before generating an offer.",
        )

    result = generate_offer(row, profile)
    row.offer_text = result["offer_text"]
    row.offer_language = result["offer_language"]
    row.offer_price_min = result["price_min"]
    row.offer_price_max = result["price_max"]
    row.offer_questions = result["questions"]
    row.offer_generated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


@router.post("/listings/{listing_id}/pipeline", response_model=ExternalListingOut)
def update_listing_pipeline(
    listing_id: str,
    body: PipelineUpdate,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if body.status not in _PIPELINE_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {sorted(_PIPELINE_STATUSES)}")
    if body.status == "won" and not body.amount_usd:
        raise HTTPException(status_code=422, detail="Wygrana wymaga podania kwoty (amount_usd).")

    row = db.get(ExternalListing, listing_id)
    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")

    now = datetime.now(timezone.utc)
    row.pipeline = body.status
    if body.status == "applied":
        row.applied_at = now
    elif body.status == "replied":
        row.replied_at = now
    elif body.status == "won":
        row.closed_at = now
        row.won_amount_usd = body.amount_usd
    elif body.status == "lost":
        row.closed_at = now
    if body.note is not None:
        row.pipeline_note = body.note
    db.commit()
    db.refresh(row)
    return row


@router.post("/listings/{listing_id}/dismiss")
def dismiss_listing(
    listing_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in ("client", "admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    row = db.get(ExternalListing, listing_id)
    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")
    row.status = "dismissed"
    db.commit()
    return {"status": "dismissed"}


# ---------------------------------------------------------------------------
# Talent (supply side)
# ---------------------------------------------------------------------------

@router.get("/talent", response_model=list[ExternalTalentOut])
def list_talent(
    source: str = "",
    skill: str = "",
    status: str = "",
    q: str = "",
    skip: int = 0,
    limit: int = Query(50, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ExternalTalent)
    if source:
        query = query.filter(ExternalTalent.source == source)
    if status:
        query = query.filter(ExternalTalent.status == status)
    if q:
        like = f"%{q}%"
        query = query.filter(ExternalTalent.name.ilike(like) | ExternalTalent.headline.ilike(like))
    rows = (query.order_by(ExternalTalent.fetched_at.desc())
            .offset(skip).limit(limit).all())
    if skill:
        s = skill.lower()
        rows = [r for r in rows if any(s in (t or "").lower() for t in (r.skills or []))]
    return rows


@router.post("/talent/{talent_id}/status")
def set_talent_status(
    talent_id: str,
    status: str = Query(..., description="contacted | invited | dismissed | new"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in ("client", "admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if status not in _TALENT_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {sorted(_TALENT_STATUSES)}")
    row = db.get(ExternalTalent, talent_id)
    if not row:
        raise HTTPException(status_code=404, detail="Talent not found")
    row.status = status
    db.commit()
    return {"status": row.status}


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@router.get("/stats")
def radar_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    def by_status(model):
        return dict(db.query(model.status, func.count(model.id)).group_by(model.status).all())

    last_scan = db.query(func.max(RadarScanLog.started_at)).scalar()

    now = datetime.now(timezone.utc)
    relevant_24h = (
        db.query(func.count(ExternalListing.id))
        .filter(ExternalListing.fit_score >= settings.RADAR_ALERT_MIN_SCORE,
                ExternalListing.fetched_at >= now - timedelta(hours=24))
        .scalar() or 0
    )
    relevant_7d = (
        db.query(func.count(ExternalListing.id))
        .filter(ExternalListing.fit_score >= settings.RADAR_ALERT_MIN_SCORE,
                ExternalListing.fetched_at >= now - timedelta(days=7))
        .scalar() or 0
    )
    pipeline_counts = dict(
        db.query(ExternalListing.pipeline, func.count(ExternalListing.id))
        .filter(ExternalListing.pipeline.isnot(None))
        .group_by(ExternalListing.pipeline).all()
    )
    sent_total = (db.query(func.count(ExternalListing.id))
                  .filter(ExternalListing.applied_at.isnot(None)).scalar() or 0)
    replied_total = (db.query(func.count(ExternalListing.id))
                      .filter(ExternalListing.replied_at.isnot(None)).scalar() or 0)
    won_total = pipeline_counts.get("won", 0)
    won_total_usd = (db.query(func.coalesce(func.sum(ExternalListing.won_amount_usd), 0.0))
                      .filter(ExternalListing.pipeline == "won").scalar() or 0.0)

    return {
        "listings": {
            "total": db.query(func.count(ExternalListing.id)).scalar() or 0,
            "by_status": by_status(ExternalListing),
        },
        "talent": {
            "total": db.query(func.count(ExternalTalent.id)).scalar() or 0,
            "by_status": by_status(ExternalTalent),
        },
        "sources_enabled": len(registry.enabled_connectors()),
        "sources_total": len(registry.ALL_CONNECTORS),
        "last_scan_at": last_scan,
        "sales_agent": {
            "relevant_24h": relevant_24h,
            "relevant_7d": relevant_7d,
            "pipeline": pipeline_counts,
            "sent_total": sent_total,
            "reply_rate": round(replied_total / sent_total, 4) if sent_total else 0.0,
            "win_rate": round(won_total / sent_total, 4) if sent_total else 0.0,
            "won_total_usd": won_total_usd,
        },
    }
