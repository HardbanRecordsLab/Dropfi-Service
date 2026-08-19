from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import User, Job, Match, Contract
from app.schemas import MatchOut, ContractOut
from app.utils.ai import score_interview, generate_price_proposal
from app.utils.notifications import create_notification
from app.utils.n8n import notify_n8n
from app.config import settings
from app.utils.fees import calculate_fee_rate

router = APIRouter(prefix="/matches", tags=["Matches"])


def _match_payload(db: Session, match: Match) -> MatchOut:
    out = MatchOut.model_validate(match)
    out.freelancer = db.get(User, match.freelancer_id)
    out.job = db.get(Job, match.job_id)
    return out


def create_contract(db: Session, match: Match, freelancer: User, autopilot: bool = False) -> Contract:
    """Shared accept logic (route + autopilot #13)."""
    match.status = "accepted"
    job = db.get(Job, match.job_id)
    if job:
        job.status = "in_progress"
        other = (
            db.query(Match)
            .filter(Match.job_id == job.id, Match.id != match.id, Match.status == "pending")
            .all()
        )
        for o in other:
            o.status = "rejected"

    amount = match.agreed_price or (job.budget if job else 0)
    fee_rate = calculate_fee_rate(freelancer)
    platform_fee = round(amount * fee_rate, 2)
    contract = Contract(
        job_id=match.job_id,
        match_id=match.id,
        client_id=match.job.client_id,
        freelancer_id=freelancer.id,
        amount=amount,
        platform_fee=platform_fee,
        fee_rate=fee_rate,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    # #5: AI-proposed milestone split
    from app.routes.contracts import create_milestones
    create_milestones(db, contract, job)

    create_notification(
        db,
        contract.client_id,
        "Freelancer accepted your job" if not autopilot else "Autopilot accepted your job",
        f"{freelancer.display_name} accepted '{job.title}'. Contract created for {amount:.2f} PLN (fee {platform_fee:.2f} PLN)."
        + (" [AI Autopilot]" if autopilot else ""),
        "match",
    )

    notify_n8n("contract-created", {
        "contract_id": contract.id,
        "job_id": contract.job_id,
        "job_title": job.title,
        "client_id": contract.client_id,
        "freelancer_id": contract.freelancer_id,
        "amount": contract.amount,
        "platform_fee": contract.platform_fee,
        "fee_rate": contract.fee_rate,
        "autopilot": autopilot,
    })
    return contract


@router.get("/job/{job_id}", response_model=list[MatchOut])
def list_job_matches(
    job_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if user.role != "client" and job.client_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the client can view these matches")
    matches = db.query(Match).filter(Match.job_id == job_id).order_by(Match.score.desc()).all()
    return [_match_payload(db, m) for m in matches]


@router.get("/mine", response_model=list[MatchOut])
def my_matches(
    user: User = Depends(require_role("freelancer")),
    db: Session = Depends(get_db),
):
    matches = (
        db.query(Match)
        .filter(Match.freelancer_id == user.id)
        .order_by(Match.created_at.desc())
        .all()
    )
    return [_match_payload(db, m) for m in matches]


@router.post("/{match_id}/accept", response_model=ContractOut)
def accept_match(
    match_id: str,
    user: User = Depends(require_role("freelancer")),
    db: Session = Depends(get_db),
):
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.freelancer_id != user.id:
        raise HTTPException(status_code=403, detail="This match is not for you")
    if match.status != "pending":
        raise HTTPException(status_code=400, detail="Match already processed")
    return create_contract(db, match, user)


@router.post("/{match_id}/interview", response_model=MatchOut)
def submit_interview(
    match_id: str,
    answers: list[str] = Body(...),
    user: User = Depends(require_role("freelancer")),
    db: Session = Depends(get_db),
):
    """#1 AI Instant Interviews: freelancer answers, AI scores (0-100) for the client."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.freelancer_id != user.id:
        raise HTTPException(status_code=403, detail="This match is not for you")
    job = db.get(Job, match.job_id)
    questions = job.interview_questions or []
    if not questions:
        raise HTTPException(status_code=400, detail="This job has no interview questions")
    if len(answers) != len(questions):
        raise HTTPException(status_code=400, detail="Number of answers must match questions")

    result = score_interview(job.title, job.description, questions, answers)
    match.interview_answers = answers
    match.interview_score = float(result["score"])
    match.interview_feedback = result["feedback"]
    match.interviewed_at = datetime.utcnow()
    db.commit()

    create_notification(
        db,
        job.client_id,
        f"Interview received: {user.display_name}",
        f"AI scored the interview {result['score']}/100 for '{job.title}'. Review it on the job page.",
        "interview",
    )
    notify_n8n("interview-submitted", {
        "match_id": match.id,
        "job_id": job.id,
        "freelancer_id": user.id,
        "score": result["score"],
    })
    return _match_payload(db, match)


@router.post("/{match_id}/propose-price", response_model=MatchOut)
def propose_price(
    match_id: str,
    amount: float = Body(..., embed=True),
    user: User = Depends(require_role("freelancer")),
    db: Session = Depends(get_db),
):
    """#3 AI Price Negotiator: freelancer proposes a price, client confirms."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.freelancer_id != user.id:
        raise HTTPException(status_code=403, detail="This match is not for you")
    if match.status != "pending":
        raise HTTPException(status_code=400, detail="Match already processed")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    match.price_proposal = round(amount, 2)
    match.price_status = "proposed"
    db.commit()

    job = db.get(Job, match.job_id)
    create_notification(
        db,
        job.client_id,
        f"Price proposal from {user.display_name}",
        f"Freelancer proposes {amount:.2f} PLN for '{job.title}' (budget: {job.budget:.2f} PLN).",
        "price",
    )
    return _match_payload(db, match)


@router.post("/{match_id}/confirm-price", response_model=MatchOut)
def confirm_price(
    match_id: str,
    user: User = Depends(require_role("client")),
    db: Session = Depends(get_db),
):
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    job = db.get(Job, match.job_id)
    if job.client_id != user.id:
        raise HTTPException(status_code=403, detail="Not your job")
    if match.price_status != "proposed" or not match.price_proposal:
        raise HTTPException(status_code=400, detail="No pending price proposal")

    match.agreed_price = match.price_proposal
    match.price_status = "accepted"
    db.commit()

    freelancer = db.get(User, match.freelancer_id)
    create_notification(
        db,
        freelancer.id,
        "Price proposal accepted!",
        f"Client agreed to {match.agreed_price:.2f} PLN for '{job.title}'. You can now accept the match.",
        "price",
    )
    return _match_payload(db, match)


@router.post("/{match_id}/decline-price", response_model=MatchOut)
def decline_price(
    match_id: str,
    user: User = Depends(require_role("client")),
    db: Session = Depends(get_db),
):
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    job = db.get(Job, match.job_id)
    if job.client_id != user.id:
        raise HTTPException(status_code=403, detail="Not your job")
    if match.price_status != "proposed":
        raise HTTPException(status_code=400, detail="No pending price proposal")

    match.price_status = "declined"
    db.commit()
    return _match_payload(db, match)


@router.post("/{match_id}/reject")
def reject_match(
    match_id: str,
    user: User = Depends(require_role("freelancer")),
    db: Session = Depends(get_db),
):
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.freelancer_id != user.id:
        raise HTTPException(status_code=403, detail="This match is not for you")
    if match.status != "pending":
        raise HTTPException(status_code=400, detail="Match already processed")
    match.status = "rejected"
    db.commit()

    # Feature #4: Best Match Guarantee — promote next candidate immediately
    from app.tasks.matching import trigger_ai_matching
    try:
        trigger_ai_matching.delay(match.job_id)
    except Exception:
        trigger_ai_matching(match.job_id)

    return {"message": "Match rejected, fallback candidates notified"}


@router.get("/{match_id}/schedule")
def match_schedule(
    match_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """#F7 Global Talent Time-Zone Auto-Scheduler: suggested overlap window."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    job = db.get(Job, match.job_id)
    freelancer = db.get(User, match.freelancer_id)
    if job.client_id != user.id and match.freelancer_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not part of this match")

    from app.utils.timezone_util import schedule_suggestion
    return schedule_suggestion(job.location, "", freelancer.location, freelancer.country)


@router.post("/{match_id}/generate", response_model=dict)
def regenerate_matches(
    match_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    job = db.get(Job, match.job_id)
    if job.client_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not your job")

    from app.tasks.matching import trigger_ai_matching
    try:
        trigger_ai_matching.delay(job.id)
    except Exception:
        trigger_ai_matching(job.id)
    return {"message": "Matching re-triggered", "job_id": job.id}
