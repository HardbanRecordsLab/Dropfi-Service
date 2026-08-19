"""Inbound integration: n8n workflows can act on DROPIFY via a signed API key.

Supported actions (payload {"action": ...}):
- {"action": "notify", "email": "...", "title": "...", "body": "..."}  → in-app notification
- {"action": "job.create", "client_email": "...", "title", "description", "budget", "deadline", ...}
  → creates a job for the client and triggers AI matching
"""
from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User, Job
from app.utils.notifications import create_notification

router = APIRouter(prefix="/n8n", tags=["n8n"])


def require_n8n_key(api_key: str | None = Header(default=None, alias="X-Dropify-Api-Key")):
    if not settings.N8N_INBOUND_KEY or api_key != settings.N8N_INBOUND_KEY:
        raise HTTPException(status_code=403, detail="Invalid n8n API key")


@router.post("/trigger", dependencies=[Depends(require_n8n_key)])
def n8n_trigger(payload: dict, db: Session = Depends(get_db)):
    action = payload.get("action", "notify")

    if action == "notify":
        email = payload.get("email", "").lower()
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        create_notification(
            db,
            user.id,
            payload.get("title", "n8n notification"),
            payload.get("body", ""),
            payload.get("type", "info"),
        )
        return {"ok": True, "notification_to": email}

    if action == "job.create":
        client_email = payload.get("client_email", "").lower()
        client = db.query(User).filter(
            User.email == client_email, User.role == "client"
        ).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        try:
            deadline = date.fromisoformat(payload.get("deadline", ""))
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="deadline must be YYYY-MM-DD")

        job = Job(
            title=payload.get("title", "Job from n8n"),
            description=payload.get("description", ""),
            budget=float(payload.get("budget", 0)),
            deadline=deadline,
            location=payload.get("location", ""),
            category=payload.get("category", ""),
            required_skills=payload.get("required_skills", []) or [],
            client_id=client.id,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        from app.tasks.matching import trigger_ai_matching
        try:
            trigger_ai_matching.delay(job.id)
        except Exception:
            trigger_ai_matching(job.id)

        return {"ok": True, "job_id": job.id, "matching": "triggered"}

    raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
