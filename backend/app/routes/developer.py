import hashlib
import secrets
from datetime import datetime

from fastapi import APIRouter, Body, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, ApiKey
from app.schemas import PartnerJobCreate
from app.utils.ai import generate_interview_questions
from app.utils.jobs import create_job_and_match

router = APIRouter(tags=["Developer / White-label API"])


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@router.post("/developer/keys")
def create_key(
    name: str = Body("API key"),
    brand_name: str = Body(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """#F8 White-Label / Reseller API: issue a partner API key so an agency can
    embed DROPIFY's AI matching as a branded service in its own portal."""
    raw = "dpk_" + secrets.token_urlsafe(32)
    key = ApiKey(
        user_id=user.id,
        name=(name or "API key")[:100],
        brand_name=(brand_name or "")[:100],
        key_prefix=raw[:12],
        key_hash=_hash_key(raw),
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return {
        "id": key.id, "name": key.name, "key": raw, "prefix": key.key_prefix,
        "warning": "Store this key now — it will not be shown again.",
    }


@router.get("/developer/keys")
def list_keys(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    keys = db.query(ApiKey).filter(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc()).all()
    return [
        {
            "id": k.id, "name": k.name, "brand_name": k.brand_name, "prefix": k.key_prefix,
            "active": k.active, "request_count": k.request_count, "last_used_at": k.last_used_at,
            "created_at": k.created_at,
        }
        for k in keys
    ]


@router.delete("/developer/keys/{key_id}")
def revoke_key(key_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    key = db.get(ApiKey, key_id)
    if not key or key.user_id != user.id:
        raise HTTPException(status_code=404, detail="Key not found")
    key.active = False
    db.commit()
    return {"message": "Key revoked"}


def _auth_partner(db: Session, x_api_key: str | None) -> ApiKey:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-Api-Key header")
    key = db.query(ApiKey).filter(ApiKey.key_hash == _hash_key(x_api_key), ApiKey.active == True).first()  # noqa: E712
    if not key:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")
    key.last_used_at = datetime.utcnow()
    key.request_count = (key.request_count or 0) + 1
    db.commit()
    return key


@router.post("/v1/external/jobs")
def partner_create_job(
    data: PartnerJobCreate,
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
    db: Session = Depends(get_db),
):
    """White-label endpoint: a partner agency's own branded portal posts a job
    (on behalf of its client) using the agency owner's DROPIFY account + AI matching."""
    key = _auth_partner(db, x_api_key)
    job = create_job_and_match(
        db,
        title=data.title,
        description=data.description,
        budget=data.budget,
        deadline=data.deadline,
        location=data.location,
        required_skills=data.required_skills,
        client_id=key.user_id,
        interview_questions=generate_interview_questions(data.title, data.description),
        source="white-label-api",
    )
    return {"job_id": job.id, "status": "created", "brand": key.brand_name or "DROPIFY"}
