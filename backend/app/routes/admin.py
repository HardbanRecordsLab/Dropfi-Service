from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import User, Job, Match, Contract, Payment
from app.schemas import AdminStats

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_role("admin"))])


@router.get("/stats", response_model=AdminStats)
def admin_stats(db: Session = Depends(get_db)):
    total_users = db.query(func.count(User.id)).scalar() or 0
    freelancers = db.query(func.count(User.id)).filter(User.role == "freelancer").scalar() or 0
    clients = db.query(func.count(User.id)).filter(User.role == "client").scalar() or 0
    jobs = db.query(func.count(Job.id)).scalar() or 0
    open_jobs = db.query(func.count(Job.id)).filter(Job.status == "open").scalar() or 0
    completed = db.query(func.count(Job.id)).filter(Job.status == "completed").scalar() or 0
    matches = db.query(func.count(Match.id)).scalar() or 0
    contracts = db.query(func.count(Contract.id)).scalar() or 0
    revenue = db.query(func.coalesce(func.sum(Payment.platform_fee), 0)).scalar() or 0

    recent_users = db.query(User).order_by(User.created_at.desc()).limit(10).all()
    return AdminStats(
        users=total_users,
        freelancers=freelancers,
        clients=clients,
        jobs=jobs,
        open_jobs=open_jobs,
        completed_jobs=completed,
        matches=matches,
        contracts=contracts,
        revenue=round(float(revenue), 2),
        recent_users=[
            {"id": u.id, "email": u.email, "role": u.role, "plan": u.plan, "created_at": str(u.created_at)}
            for u in recent_users
        ],
    )


@router.get("/disputes", response_model=list[dict])
def admin_disputes(db: Session = Depends(get_db)):
    contracts = (
        db.query(Contract)
        .filter(Contract.status == "disputed")
        .order_by(Contract.disputed_at.desc())
        .all()
    )
    result = []
    for c in contracts:
        job = db.get(Job, c.job_id)
        client = db.get(User, c.client_id)
        freelancer = db.get(User, c.freelancer_id)
        result.append({
            "id": c.id,
            "job_title": job.title if job else c.job_id,
            "amount": c.amount,
            "client_email": client.email if client else "",
            "freelancer_email": freelancer.email if freelancer else "",
            "dispute_reason": c.dispute_reason,
            "dispute_raised_by": c.dispute_raised_by,
            "dispute_ai_assessment": c.dispute_ai_assessment,
            "disputed_at": str(c.disputed_at) if c.disputed_at else None,
        })
    return result


@router.get("/users", response_model=list[dict])
def admin_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).limit(100).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "plan": u.plan,
            "rating": u.rating,
            "total_jobs": u.total_jobs,
            "is_active": u.is_active,
            "created_at": str(u.created_at),
        }
        for u in users
    ]


@router.get("/verification-queue", response_model=dict)
def admin_verification_queue(db: Session = Depends(get_db)):
    """Freelancer profiles and job postings the AI check flagged or wants a
    human to look at (verification_status in review|flagged) — the actual,
    reviewable output of verify_freelancer_profile / verify_job_posting, not
    just a score sitting unused in the database."""
    users = (
        db.query(User)
        .filter(User.verification_status.in_(["review", "flagged"]))
        .order_by(User.verification_score.asc().nullslast())
        .limit(100)
        .all()
    )
    jobs = (
        db.query(Job)
        .filter(Job.verification_status.in_(["review", "flagged"]))
        .order_by(Job.verification_score.asc().nullslast())
        .limit(100)
        .all()
    )
    return {
        "freelancers": [
            {
                "id": u.id,
                "email": u.email,
                "name": u.display_name,
                "score": u.verification_score,
                "status": u.verification_status,
                "flags": u.verification_flags,
                "summary": u.verification_summary,
                "verified_at": str(u.verified_at) if u.verified_at else None,
            }
            for u in users
        ],
        "jobs": [
            {
                "id": j.id,
                "title": j.title,
                "client_id": j.client_id,
                "budget": j.budget,
                "score": j.verification_score,
                "status": j.verification_status,
                "flags": j.verification_flags,
                "summary": j.verification_summary,
                "verified_at": str(j.verified_at) if j.verified_at else None,
            }
            for j in jobs
        ],
    }
