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
from app.schemas import ExternalListingOut, ExternalTalentOut, RadarSourceOut
from app.utils.jobs import create_job_and_match
from app.utils.security import hash_password, make_referral_code

router = APIRouter(prefix="/radar", tags=["Portal Radar"])
logger = logging.getLogger(__name__)

_TALENT_STATUSES = {"new", "contacted", "invited", "dismissed"}


def _radar_bot(db: Session) -> User:
    """The client account that owns jobs imported from external leads."""
    bot = db.query(User).filter(User.email == settings.RADAR_BOT_EMAIL).first()
    if bot is None:
        import secrets
        bot = User(
            email=settings.RADAR_BOT_EMAIL,
            password_hash=hash_password(secrets.token_urlsafe(24)),
            role="client",
            first_name="Portal",
            last_name="Radar",
            company="DROPIFY Portal Radar",
            is_active=True,
            referral_code=make_referral_code(settings.RADAR_BOT_EMAIL),
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)
    return bot


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
    return (query.order_by(ExternalListing.fetched_at.desc())
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

    bot = _radar_bot(db)
    budget = row.budget_max or row.budget_min or 500.0
    description = (
        f"{row.description}\n\n"
        f"---\nŹródło / Source: {row.source} — {row.url}\n"
        f"Firma / Company: {row.company or 'n/a'}\n"
        f"Lokalizacja / Location: {row.location or 'n/a'}"
        + (f"\nKontakt / Contact: {row.contact}" if row.contact else "")
    )
    job = create_job_and_match(
        db,
        title=row.title,
        description=description,
        budget=float(budget),
        deadline=date.today() + timedelta(days=14),
        location=row.location or ("Remote" if row.is_remote else ""),
        category=row.category or "",
        required_skills=[t for t in (row.tags or []) if isinstance(t, str)][:8],
        client_id=bot.id,
        source=f"radar:{row.source}",
    )
    job.external_source = row.source
    job.external_url = row.url
    row.status = "imported"
    row.imported_job_id = job.id
    db.commit()
    return {"status": "imported", "job_id": job.id}


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
    }
