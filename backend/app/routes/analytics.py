from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, Job, Match, Contract, Rating
from app.schemas import AnalyticsOut

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=AnalyticsOut)
def dashboard_analytics(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    month_start = now.replace(day=1)
    result = AnalyticsOut(role=user.role)

    if user.role == "client":
        my_jobs = db.query(Job).filter(Job.client_id == user.id).all()
        job_ids = [j.id for j in my_jobs]
        result.total_jobs = len(my_jobs)
        result.active_jobs = sum(1 for j in my_jobs if j.status in ("open", "matched", "in_progress"))
        result.completed_jobs = sum(1 for j in my_jobs if j.status == "completed")
        result.jobs_this_month = sum(1 for j in my_jobs if j.created_at and j.created_at >= month_start)

        contracts = db.query(Contract).filter(Contract.client_id == user.id).all()
        result.total_spent = round(sum(c.amount for c in contracts if c.status == "completed"), 2)

        matches = (
            db.query(Match).filter(Match.job_id.in_(job_ids)).order_by(Match.created_at.desc()).all()
            if job_ids else []
        )
        result.match_count = len(matches)
        result.pending_matches = sum(1 for m in matches if m.status == "pending")
        result.accepted_matches = sum(1 for m in matches if m.status == "accepted")

        # Feature #18: time-to-hire metrics
        match_times = []
        instant = 0
        for j in my_jobs:
            if not j.created_at:
                continue
            first_match = (
                db.query(Match)
                .filter(Match.job_id == j.id)
                .order_by(Match.created_at.asc())
                .first()
            )
            if first_match and first_match.created_at:
                delta = (first_match.created_at - j.created_at).total_seconds()
                match_times.append(delta)
                if delta < 60:
                    instant += 1
        if match_times:
            result.avg_match_time_seconds = round(sum(match_times) / len(match_times))
        result.instant_matches = instant

        hire_times = []
        for c in contracts:
            job = db.get(Job, c.job_id)
            if job and job.created_at and c.created_at:
                hire_times.append((c.created_at - job.created_at).total_seconds())
        if hire_times:
            result.avg_time_to_hire_hours = round(sum(hire_times) / len(hire_times) / 3600, 1)

        result.recent_jobs = [j.id for j in sorted(my_jobs, key=lambda x: x.created_at, reverse=True)[:8]]
        result.recent_matches = [m.id for m in matches[:8]]

    else:
        my_matches = db.query(Match).filter(Match.freelancer_id == user.id).all()
        result.match_count = len(my_matches)
        result.pending_matches = sum(1 for m in my_matches if m.status == "pending")
        result.accepted_matches = sum(1 for m in my_matches if m.status == "accepted")

        contracts = db.query(Contract).filter(Contract.freelancer_id == user.id).all()
        result.completed_jobs = sum(1 for c in contracts if c.status == "completed")
        result.total_earned = round(sum(c.amount - c.platform_fee for c in contracts if c.status == "completed"), 2)
        result.jobs_this_month = sum(1 for c in contracts if c.created_at and c.created_at >= month_start)

        open_jobs = db.query(Job).filter(Job.status == "open").count()
        result.active_jobs = open_jobs
        result.recent_matches = [m.id for m in my_matches[:8]]

    ratings = db.query(Rating).filter(Rating.to_user_id == user.id).all()
    if ratings:
        result.rating = round(sum(r.score for r in ratings) / len(ratings), 2)

    return result
