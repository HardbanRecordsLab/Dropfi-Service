"""Shared helper: create a Job and kick off the AI matching pipeline the same
way everywhere a job can originate (web UI, white-label partner API, store
syncs) — used by routes/jobs.py, routes/developer.py, routes/integrations.py."""
from datetime import date

from sqlalchemy.orm import Session

from app.models import Job
from app.utils.n8n import notify_n8n


def create_job_and_match(
    db: Session,
    *,
    title: str,
    description: str,
    budget: float,
    deadline: date,
    client_id: str,
    category: str = "",
    location: str = "",
    required_skills: list | None = None,
    interview_questions: list | None = None,
    source: str = "web",
) -> Job:
    job = Job(
        title=title[:255],
        description=description,
        budget=budget,
        deadline=deadline,
        location=location,
        category=category,
        required_skills=required_skills or [],
        client_id=client_id,
        interview_questions=interview_questions,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    from app.tasks.matching import trigger_ai_matching
    try:
        trigger_ai_matching.delay(job.id)
    except Exception:
        # Celery not running -> run inline so the platform is "self-working"
        trigger_ai_matching(job.id)
    db.refresh(job)

    notify_n8n("job-created", {
        "job_id": job.id, "title": job.title, "budget": job.budget,
        "deadline": str(job.deadline), "category": job.category,
        "location": job.location, "client_id": job.client_id, "source": source,
    })
    return job
