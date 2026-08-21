from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role, get_current_user
from app.models import User, Listing
from app.utils.ai import generate_listing, generate_video_script, generate_source_finder_plan
from app.utils.jobs import create_job_and_match

router = APIRouter(prefix="/factory", tags=["AI Factory"])


@router.post("/listing")
def create_listing(
    product_name: str = Body(...),
    description: str = Body(""),
    source_url: str = Body(""),
    language: str = Body("pl"),
    marketplace: str = Body("generic"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """#F1 AI Listing Factory: generate a full multi-marketplace product listing
    (title, description, bullets, SEO tags) from a product name/URL/photo notes."""
    content = generate_listing(product_name, description, source_url, language, marketplace)
    listing = Listing(
        user_id=user.id,
        product_name=product_name[:255],
        source_url=source_url[:500],
        language=language,
        marketplace=marketplace,
        content=content,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return {"id": listing.id, "content": content}


@router.post("/video-script")
def create_video_script(
    product_name: str = Body(...),
    description: str = Body(""),
    language: str = Body("pl"),
    user: User = Depends(get_current_user),
):
    """#F6 Marketing Video Script & Voiceover Generator (TikTok/Reels ad script)."""
    return generate_video_script(product_name, description, language)


@router.post("/source-finder")
def source_finder(
    product_ref: str = Body(...),
    notes: str = Body(""),
    language: str = Body("pl"),
    user: User = Depends(get_current_user),
):
    """Sprint 4 #12 Product Source Finder: paste a product link/name, get a
    full fulfillment plan (suggested jobs + budgets) in ~30 seconds."""
    return generate_source_finder_plan(product_ref, notes, language)


@router.post("/source-finder/create-jobs")
def source_finder_create_jobs(
    jobs: list[dict] = Body(..., embed=True),
    user: User = Depends(require_role("client")),
    db: Session = Depends(get_db),
):
    """One-click: turn Product Source Finder suggestions into real, AI-matched
    DROPIFY jobs (each item: {category, title, description, suggested_budget})."""
    created = []
    for item in jobs[:10]:
        job = create_job_and_match(
            db,
            title=str(item.get("title", "New job"))[:255],
            description=str(item.get("description", "")) or str(item.get("title", "")),
            budget=float(item.get("suggested_budget") or 500),
            deadline=date.today() + timedelta(days=10),
            category=str(item.get("category", "")),
            client_id=user.id,
            source="source-finder",
        )
        created.append(job.id)
    return {"created_job_ids": created}


@router.get("/history")
def listing_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(Listing)
        .filter(Listing.user_id == user.id)
        .order_by(Listing.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": i.id, "product_name": i.product_name, "marketplace": i.marketplace,
            "language": i.language, "content": i.content, "created_at": i.created_at,
        }
        for i in items
    ]
