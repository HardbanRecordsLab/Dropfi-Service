from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, Job, Contract, CopilotMessage
from app.utils.ai import answer_copilot

router = APIRouter(prefix="/copilot", tags=["AI Co-Pilot"])


def _assert_participant(db: Session, job: Job, user: User) -> Contract | None:
    contract = db.query(Contract).filter(Contract.job_id == job.id).first()
    allowed = job.client_id == user.id or (contract and contract.freelancer_id == user.id) or user.role == "admin"
    if not allowed:
        raise HTTPException(status_code=403, detail="Not part of this job")
    return contract


@router.post("/ask")
def ask_copilot(
    job_id: str = Body(...),
    question: str = Body(..., min_length=3),
    language: str = Body("en"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """#F5 AI Co-Pilot: in-job assistant answering questions grounded in job context."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    contract = _assert_participant(db, job, user)

    context_parts = [f"Status: {job.status}", f"Budget: {job.budget} PLN"]
    if job.ai_analysis:
        context_parts.append(f"AI analysis: {job.ai_analysis}")
    if contract:
        context_parts.append(f"Contract amount: {contract.amount} PLN, fee: {contract.platform_fee} PLN")

    answer = answer_copilot(job.title, job.description, " | ".join(context_parts), question, language)

    msg = CopilotMessage(job_id=job_id, user_id=user.id, question=question, answer=answer)
    db.add(msg)
    db.commit()
    return {"answer": answer}


@router.get("/history/{job_id}")
def copilot_history(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    _assert_participant(db, job, user)
    msgs = (
        db.query(CopilotMessage)
        .filter(CopilotMessage.job_id == job_id, CopilotMessage.user_id == user.id)
        .order_by(CopilotMessage.created_at)
        .limit(50)
        .all()
    )
    return [{"question": m.question, "answer": m.answer, "created_at": m.created_at} for m in msgs]
