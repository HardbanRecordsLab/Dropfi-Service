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
