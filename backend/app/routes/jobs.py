import json
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_optional_user, require_role
from app.models import User, Job, Match, Contract, Milestone
from app.schemas import JobCreate, JobUpdate, JobOut, JobListItem
from app.utils.ai import (
    analyze_job, embed_text, job_search_text,
    generate_interview_questions, generate_job_draft,
    check_deliverables, generate_price_proposal,
)
from app.utils.notifications import create_notification
from app.utils.n8n import notify_n8n
from app.utils.jobs import create_job_and_match

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobOut, status_code=201)
def create_job(
    data: JobCreate,
    user: User = Depends(require_role("client")),
    db: Session = Depends(get_db),
):
    job = create_job_and_match(
        db,
        title=data.title,
        description=data.description,
        budget=data.budget,
        deadline=data.deadline,
        location=data.location,
        required_skills=data.required_skills,
        category=data.category,
        client_id=user.id,
        interview_questions=data.interview_questions or generate_interview_questions(data.title, data.description),
        source="web",
    )
    return job


@router.get("/mine", response_model=list[JobListItem])
def my_jobs(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jobs = db.query(Job).filter(Job.client_id == user.id).order_by(Job.created_at.desc()).all()
    return _with_match_counts(db, jobs)


@router.get("", response_model=list[JobListItem])
def list_jobs(
    category: str = "",
    status: str = "open",
    search: str = "",
    location: str = "",
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Job)
    if status:
        q = q.filter(Job.status == status)
    if category:
        q = q.filter(Job.category == category)
    if location:
        q = q.filter(Job.location.ilike(f"%{location}%"))
    if search:
        like = f"%{search.lower()}%"
        q = q.filter(Job.title.ilike(like) | Job.description.ilike(like))
    jobs = q.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    return _with_match_counts(db, jobs)


@router.get("/recommended", response_model=list[JobListItem])
def recommended_jobs(
    user: User = Depends(require_role("freelancer")),
    db: Session = Depends(get_db),
):
    """Freelancer view: open jobs ranked by similarity to their profile."""
    skills = set(user.skills or [])
    q = db.query(Job).filter(Job.status == "open").order_by(Job.created_at.desc()).limit(200).all()

    def rank(job: Job) -> float:
        job_skills = set(job.required_skills or [])
        skill_overlap = len(skills & job_skills) / max(1, len(skills | job_skills))
        days_left = (job.deadline - datetime.now(timezone.utc).date()).days
        recency = 1.0 if days_left >= 7 else (0.7 if days_left >= 3 else 0.3)
        return skill_overlap * 0.6 + recency * 0.2 + (1.0 / (1 + job.budget / 5000)) * 0.2

    q.sort(key=rank, reverse=True)
    return _with_match_counts(db, q[:50])


@router.post("/generate", response_model=dict)
def generate_job_post(
    idea: str = Body(..., embed=True),
    user: User = Depends(get_current_user),
):
    """#14 AI Onboarding: one sentence → complete job post draft."""
    if len(idea.strip()) < 10:
        raise HTTPException(status_code=400, detail="Describe your idea in at least 10 characters")
    draft = generate_job_draft(idea)
    return {"draft": draft}


@router.post("/{job_id}/deliverables", response_model=JobOut)
def submit_deliverables(
    job_id: str,
    description: str = Body(..., embed=True),
    url: str = Body("", embed=True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """#2 AI Deliverable Checker: freelancer submits work, AI QA report generated."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    contract = _active_contract(db, job.id)
    if not contract:
        raise HTTPException(status_code=400, detail="No contract for this job")
    if user.role == "freelancer" and contract.freelancer_id != user.id:
        raise HTTPException(status_code=403, detail="You are not the freelancer on this job")
    if user.role == "client" and contract.client_id != user.id:
        raise HTTPException(status_code=403, detail="You are not the client on this job")

    report = check_deliverables(
        job.title, job.description, job.ai_analysis,
        description, url,
    )
    job.deliverables = description
    job.deliverable_url = url
    job.deliverable_report = report
    db.commit()

    other_party = db.get(User, contract.freelancer_id if user.role == "client" else contract.client_id)
    create_notification(
        db,
        other_party.id,
        "Deliverables submitted + AI QA report",
        f"AI Deliverable Checker scored the work {report.get('score', 0)}/100 "
        f"({report.get('recommendation', 'review')}). Review it on the job page.",
        "deliverable",
    )
    notify_n8n("deliverables-checked", {
        "job_id": job.id,
        "score": report.get("score"),
        "recommendation": report.get("recommendation"),
    })
    db.refresh(job)
    return job


@router.get("/{job_id}/fair-price", response_model=dict)
def job_fair_price(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """#3 AI Price Negotiator: AI fair-price window + rationale."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    fair_price = float((job.ai_analysis or {}).get("fair_price") or job.budget)
    return generate_price_proposal(job.title, job.description, job.budget, fair_price)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, user: User | None = Depends(get_optional_user), db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    out = JobOut.model_validate(job)
    participant = user is not None and (
        user.role == "admin" or user.id == job.client_id
        or db.query(Contract).filter(Contract.job_id == job.id, Contract.freelancer_id == user.id).first() is not None
    )
    if not participant:  # delivered work is private to the parties
        out.deliverables = None
        out.deliverable_url = None
        out.deliverable_report = None
    return out


def _active_contract(db: Session, job_id: str) -> Contract | None:
    """The live contract of a job (a refund reopens the job, so older cancelled ones may exist)."""
    return (
        db.query(Contract)
        .filter(Contract.job_id == job_id)
        .order_by((Contract.status.in_(["in_progress", "disputed"])).desc(), Contract.created_at.desc())
        .first()
    )


@router.put("/{job_id}", response_model=JobOut)
def update_job(
    job_id: str,
    data: JobUpdate,
    user: User = Depends(require_role("client")),
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.client_id != user.id:
        raise HTTPException(status_code=403, detail="Not your job")
    live = db.query(Contract).filter(Contract.job_id == job.id, Contract.status.in_(["in_progress", "disputed"])).first()
    if live:
        raise HTTPException(status_code=409, detail="This job has an active contract — it can no longer be edited")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}")
def delete_job(
    job_id: str,
    user: User = Depends(require_role("client")),
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.client_id != user.id:
        raise HTTPException(status_code=403, detail="Not your job")
    if db.query(Contract).filter(Contract.job_id == job.id).first():
        # Contracts carry payments/invoices — keep the audit trail, just close the job.
        raise HTTPException(status_code=409, detail="Jobs with a contract cannot be deleted — cancel it instead")
    from app.models import Message
    match_ids = [m.id for m in db.query(Match.id).filter(Match.job_id == job.id).all()]
    if match_ids:
        db.query(Message).filter(Message.match_id.in_(match_ids)).delete(synchronize_session=False)
    db.delete(job)
    db.commit()
    return {"message": "Job deleted"}


@router.post("/{job_id}/complete", response_model=JobOut)
def complete_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Client: closes the job. With a contract this only works once every milestone
    is released (escrow drives completion — see contracts.finalize_milestone_release).
    Freelancer: signals 'work done' to the client; it does not close anything, so a
    no-show can't block the refund guarantee or a dispute."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    contract = _active_contract(db, job.id)

    if user.role == "client":
        if job.client_id != user.id:
            raise HTTPException(status_code=403, detail="Not your job")
        if job.status == "completed":
            raise HTTPException(status_code=400, detail="Job already completed")
        if contract and contract.status == "in_progress":
            unreleased = (db.query(Milestone)
                          .filter(Milestone.contract_id == contract.id, Milestone.status != "released").count())
            if unreleased:
                raise HTTPException(status_code=400, detail="Release the remaining milestones first — the contract completes automatically")
            from app.routes.contracts import _count_completion
            contract.status = "completed"
            contract.completed_at = datetime.now(timezone.utc)
            _count_completion(db, contract)
        elif contract and contract.status == "disputed":
            raise HTTPException(status_code=409, detail="This contract is disputed — wait for the resolution")
        job.status = "completed"
    elif user.role == "freelancer":
        if not contract or contract.freelancer_id != user.id:
            raise HTTPException(status_code=403, detail="No active contract for this job")
        if contract.status != "in_progress":
            raise HTTPException(status_code=400, detail="Contract already closed")
        create_notification(
            db,
            job.client_id,
            "Freelancer reports the job as done",
            f"The freelancer marked '{job.title}' as finished. Review the work and release the remaining milestones.",
            "info",
        )
    else:
        raise HTTPException(status_code=403, detail="Admins cannot complete jobs")

    db.commit()
    db.refresh(job)

    notify_n8n("job-completed" if user.role == "client" else "job-done-reported", {
        "job_id": job.id,
        "title": job.title,
        "completed_by": user.role,
        "budget": job.budget,
    })
    return job


def _with_match_counts(db: Session, jobs: list[Job]) -> list[JobListItem]:
    result = []
    for job in jobs:
        item = JobListItem.model_validate(job)
        item.match_count = (
            db.query(Match).filter(Match.job_id == job.id, Match.status == "accepted").count()
            + db.query(Match).filter(Match.job_id == job.id, Match.status == "pending").count()
        )
        result.append(item)
    return result
