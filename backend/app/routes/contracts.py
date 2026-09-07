from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import User, Job, Contract, Payment, Milestone, Match
from app.schemas import ContractOut, MilestoneOut
from app.utils.fees import calculate_fee_rate
from app.utils.n8n import notify_n8n
from app.utils.notifications import create_notification

router = APIRouter(prefix="/contracts", tags=["Contracts"])

AUTO_RELEASE_HOURS = 48
REFUND_NO_SHOW_DAYS = 3


def create_milestones(db: Session, contract: Contract, job: Job) -> list[Milestone]:
    """#5: AI-proposed milestone split, created with the contract."""
    from app.utils.ai import generate_milestones
    items = generate_milestones(job.title, job.description, contract.amount, job.ai_analysis)
    milestones = []
    for i, item in enumerate(items):
        m = Milestone(
            contract_id=contract.id,
            title=item["title"],
            amount=round(float(item["amount"]), 2),
            order_index=i,
        )
        db.add(m)
        milestones.append(m)
    db.commit()
    return milestones


def _contract_payload(db: Session, contract: Contract, for_user: User | None = None) -> ContractOut:
    out = ContractOut.model_validate(contract)
    out.freelancer = db.get(User, contract.freelancer_id)
    milestones = (
        db.query(Milestone)
        .filter(Milestone.contract_id == contract.id)
        .order_by(Milestone.order_index)
        .all()
    )
    out.milestones = [MilestoneOut.model_validate(m) for m in milestones]
    out.released_amount = round(sum(m.amount for m in milestones if m.status == "released"), 2)

    if for_user and for_user.role == "client" and contract.client_id == for_user.id:
        out.refund_eligible, out.refund_reason = refund_eligibility(db, contract)
    return out


def refund_eligibility(db: Session, contract: Contract) -> tuple[bool, str]:
    """#7 Deposit Refund Guarantee: no-show freelancer → client gets money back."""
    if contract.status != "in_progress":
        return False, "Contract is not in progress"
    age = datetime.now(timezone.utc).replace(tzinfo=None) - contract.created_at
    if age < timedelta(days=REFUND_NO_SHOW_DAYS):
        return False, f"Refund available after {REFUND_NO_SHOW_DAYS} days without work ({REFUND_NO_SHOW_DAYS - age.days} day(s) left)"
    milestones = (
        db.query(Milestone)
        .filter(Milestone.contract_id == contract.id, Milestone.status.in_(["in_review", "released"]))
        .count()
    )
    if milestones > 0:
        return False, "Freelancer already submitted work — refund not available"
    return True, "Freelancer has not started work — refund guarantee applies"


@router.get("/mine", response_model=list[ContractOut])
def my_contracts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role == "client":
        contracts = db.query(Contract).filter(Contract.client_id == user.id).order_by(Contract.created_at.desc()).all()
    else:
        contracts = db.query(Contract).filter(Contract.freelancer_id == user.id).order_by(Contract.created_at.desc()).all()
    return [_contract_payload(db, c, user) for c in contracts]


@router.get("/{contract_id}", response_model=ContractOut)
def contract_detail(
    contract_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.client_id != user.id and contract.freelancer_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not your contract")
    return _contract_payload(db, contract, user)


@router.post("/{contract_id}/milestones/{milestone_id}/submit", response_model=ContractOut)
def submit_milestone(
    contract_id: str,
    milestone_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """#5: freelancer delivers a milestone → in_review (client releases or auto-release after 48h)."""
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.freelancer_id != user.id:
        raise HTTPException(status_code=403, detail="Only the freelancer can submit milestones")
    milestone = db.get(Milestone, milestone_id)
    if not milestone or milestone.contract_id != contract.id:
        raise HTTPException(status_code=404, detail="Milestone not found")
    if milestone.status != "pending":
        raise HTTPException(status_code=400, detail="Milestone already processed")
    if not _previous_released(db, milestone):
        raise HTTPException(status_code=400, detail="Previous milestones must be released first")

    milestone.status = "in_review"
    milestone.submitted_at = datetime.now(timezone.utc)
    db.commit()

    create_notification(
        db,
        contract.client_id,
        f"Milestone submitted: {milestone.title}",
        f"Freelancer delivered '{milestone.title}' ({milestone.amount:.2f} PLN). "
        f"Release it or it auto-releases after {AUTO_RELEASE_HOURS}h.",
        "milestone",
    )
    notify_n8n("milestone-submitted", {
        "contract_id": contract.id,
        "milestone_id": milestone.id,
        "title": milestone.title,
        "amount": milestone.amount,
    })
    return _contract_payload(db, contract, user)


@router.post("/{contract_id}/milestones/{milestone_id}/release", response_model=ContractOut)
def release_milestone(
    contract_id: str,
    milestone_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """#5: client releases milestone payment → Payment created; contract auto-completes when all released."""
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.client_id != user.id:
        raise HTTPException(status_code=403, detail="Only the client can release payments")
    milestone = db.get(Milestone, milestone_id)
    if not milestone or milestone.contract_id != contract.id:
        raise HTTPException(status_code=404, detail="Milestone not found")
    if milestone.status != "in_review":
        raise HTTPException(status_code=400, detail="Milestone must be in review to release")

    _release(db, contract, milestone)
    return _contract_payload(db, contract, user)


@router.post("/{contract_id}/request-refund", response_model=ContractOut)
def request_refund(
    contract_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """#7 Deposit Refund Guarantee: AI-verified no-show → cancel contract, refund, reopen job."""
    if user.role != "client":
        raise HTTPException(status_code=403, detail="Only clients can request a refund")
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.client_id != user.id:
        raise HTTPException(status_code=403, detail="Only the client can request a refund")

    eligible, reason = refund_eligibility(db, contract)
    if not eligible:
        raise HTTPException(status_code=400, detail=reason)

    contract.status = "cancelled"
    job = db.get(Job, contract.job_id)
    if job:
        job.status = "open"  # reopen for new candidates (fallback chain #4)

    from app.routes.payments import refund_stripe_payment

    refunded = 0
    refund_failures = 0
    payments = db.query(Payment).filter(Payment.contract_id == contract.id).all()
    for payment in payments:
        if payment.status in ("paid", "pending"):
            if refund_stripe_payment(payment):
                payment.status = "refunded"
                refunded += payment.amount
            else:
                # Real Stripe charge exists but the refund API call failed — do NOT
                # mark it 'refunded' in the DB (that would be an accounting lie).
                # Contract still gets cancelled; this needs manual operator follow-up.
                refund_failures += 1
    db.commit()

    freelancer = db.get(User, contract.freelancer_id)
    create_notification(
        db,
        contract.freelancer_id,
        "Contract cancelled — refund issued",
        f"Client was refunded {refunded:.2f} PLN for '{job.title}' because no work was started. "
        "AI verified the no-show automatically.",
        "refund",
    )
    create_notification(
        db,
        contract.client_id,
        "Refund issued" if not refund_failures else "Refund in progress",
        (
            f"Your deposit for '{job.title}' was refunded ({refunded:.2f} PLN). "
            "AI matching is looking for a new freelancer."
        ) if not refund_failures else (
            f"Your refund for '{job.title}' could not be completed automatically. "
            "Our team has been alerted and will process it manually."
        ),
        "refund",
    )
    notify_n8n("refund-issued", {
        "contract_id": contract.id,
        "job_id": contract.job_id,
        "refunded": refunded,
        "refund_failures": refund_failures,
    })

    # Best Match Guarantee synergy: re-match the reopened job
    from app.tasks.matching import trigger_ai_matching
    try:
        trigger_ai_matching.delay(job.id)
    except Exception:
        trigger_ai_matching(job.id)

    return _contract_payload(db, contract, user)


@router.get("/{contract_id}/agreement")
def contract_agreement(
    contract_id: str,
    language: str = "en",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """#F3 AI Contract & Compliance Generator: plain-language, jurisdiction-aware
    service agreement text, generated on demand for the contract's two parties."""
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.client_id != user.id and contract.freelancer_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not your contract")

    job = db.get(Job, contract.job_id)
    client = db.get(User, contract.client_id)
    freelancer = db.get(User, contract.freelancer_id)

    from app.utils.ai import generate_contract_agreement
    from app.utils.currency import tax_hint
    note = tax_hint(client.country if client else "")["note"]
    text = generate_contract_agreement(contract, job, client, freelancer, note, language)
    return {"agreement": text}


@router.post("/{contract_id}/dispute", response_model=ContractOut)
def raise_dispute(
    contract_id: str,
    reason: str = Body(..., min_length=10, embed=True),
    language: str = Body("en", embed=True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Either party can raise a dispute. AI gives the admin a neutral
    first-pass assessment (semi-automated per doku's original design) — it
    never resolves the dispute on its own; only an admin can (see below)."""
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if user.id not in (contract.client_id, contract.freelancer_id):
        raise HTTPException(status_code=403, detail="Not your contract")
    if contract.status not in ("in_progress",):
        raise HTTPException(status_code=400, detail="Only an in-progress contract can be disputed")

    job = db.get(Job, contract.job_id)
    from app.utils.ai import generate_dispute_mediation
    mediation = generate_dispute_mediation(job.title, job.description, reason, contract.amount, language)

    contract.status = "disputed"
    contract.dispute_reason = reason
    contract.dispute_raised_by = "client" if user.id == contract.client_id else "freelancer"
    contract.dispute_ai_assessment = mediation.get("assessment", "")
    contract.disputed_at = datetime.now(timezone.utc)
    db.commit()

    other_party_id = contract.freelancer_id if user.id == contract.client_id else contract.client_id
    create_notification(
        db, other_party_id, "Contract disputed",
        f"A dispute was raised on '{job.title}'. Our team will review it shortly.", "dispute",
    )
    for admin in db.query(User).filter(User.role == "admin").all():
        create_notification(
            db, admin.id, f"⚠️ Dispute: {job.title}",
            f"Reason: {reason[:200]} | AI assessment: {mediation.get('assessment', '')[:200]} "
            f"| AI suggests: {mediation.get('suggested_resolution', 'manual_review')}",
            "dispute",
        )
    notify_n8n("contract-disputed", {
        "contract_id": contract.id, "job_id": contract.job_id,
        "raised_by": contract.dispute_raised_by, "ai_suggestion": mediation.get("suggested_resolution"),
    })
    return _contract_payload(db, contract, user)


@router.post("/{contract_id}/resolve-dispute", response_model=ContractOut)
def resolve_dispute(
    contract_id: str,
    resolution: str = Body(..., embed=True),
    freelancer_pct: float = Body(100.0, embed=True),
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Admin-only, final arbiter (doku: 'owner is final arbiter'). Three
    resolutions:
    - release_to_freelancer: release everything to the freelancer
    - refund_client: refund everything to the client
    - proportional: split by freelancer_pct (0-100) — release % to freelancer, refund rest to client
    """
    if resolution not in ("release_to_freelancer", "refund_client", "proportional"):
        raise HTTPException(status_code=400, detail="resolution must be 'release_to_freelancer', 'refund_client', or 'proportional'")
    if resolution == "proportional" and not (0 <= freelancer_pct <= 100):
        raise HTTPException(status_code=400, detail="freelancer_pct must be between 0 and 100")

    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.status != "disputed":
        raise HTTPException(status_code=400, detail="Contract is not disputed")

    remaining = (
        db.query(Milestone)
        .filter(Milestone.contract_id == contract.id, Milestone.status != "released")
        .order_by(Milestone.order_index)
        .all()
    )

    if resolution == "release_to_freelancer":
        freelancer = db.get(User, contract.freelancer_id)
        for m in remaining:
            fee = round(m.amount * (contract.fee_rate or 0.08), 2)
            db.add(Payment(
                contract_id=contract.id, milestone_id=m.id, amount=round(m.amount, 2),
                platform_fee=fee, net_amount=round(m.amount - fee, 2), status="paid",
                provider="admin_override",
                payout_method=freelancer.payout_method if freelancer else "bank",
                payout_address=freelancer.payout_address if freelancer else None,
            ))
            db.commit()
            finalize_milestone_release(db, contract, m)  # sets contract.status="completed" on the last one
    elif resolution == "proportional":
        from app.routes.payments import refund_stripe_payment
        freelancer = db.get(User, contract.freelancer_id)
        pct = freelancer_pct / 100.0
        for m in remaining:
            freelancer_amount = round(m.amount * pct, 2)
            client_refund_amount = round(m.amount - freelancer_amount, 2)
            # Release portion to freelancer
            if freelancer_amount > 0:
                fee = round(freelancer_amount * (contract.fee_rate or 0.08), 2)
                db.add(Payment(
                    contract_id=contract.id, milestone_id=m.id, amount=freelancer_amount,
                    platform_fee=fee, net_amount=round(freelancer_amount - fee, 2), status="paid",
                    provider="admin_override",
                    payout_method=freelancer.payout_method if freelancer else "bank",
                    payout_address=freelancer.payout_address if freelancer else None,
                ))
                db.commit()
                m.status = "released"
                m.released_at = datetime.now(timezone.utc)
            # Refund portion to client
            if client_refund_amount > 0:
                payment = db.query(Payment).filter(Payment.milestone_id == m.id).first()
                if payment and payment.status in ("paid", "pending"):
                    if refund_stripe_payment(payment):
                        payment.status = "refunded"
            if freelancer_amount <= 0:
                m.status = "rejected"
        contract.status = "completed"
    else:
        from app.routes.payments import refund_stripe_payment
        for m in remaining:
            payment = db.query(Payment).filter(Payment.milestone_id == m.id).first()
            if payment and payment.status in ("paid", "pending"):
                if refund_stripe_payment(payment):
                    payment.status = "refunded"
            m.status = "rejected"
        contract.status = "cancelled"
        job = db.get(Job, contract.job_id)
        if job:
            job.status = "open"

    contract.dispute_resolution = resolution
    contract.resolved_at = datetime.now(timezone.utc)
    db.commit()

    job = db.get(Job, contract.job_id)
    for party_id in (contract.client_id, contract.freelancer_id):
        create_notification(
            db, party_id, "Dispute resolved",
            f"The dispute on '{job.title if job else contract.job_id}' was resolved: {resolution.replace('_', ' ')}.",
            "dispute",
        )
    notify_n8n("dispute-resolved", {"contract_id": contract.id, "resolution": resolution})
    return _contract_payload(db, contract, admin)


def _previous_released(db: Session, milestone: Milestone) -> bool:
    previous = (
        db.query(Milestone)
        .filter(Milestone.contract_id == milestone.contract_id, Milestone.order_index < milestone.order_index)
        .count()
    )
    if previous == 0:
        return True
    released = (
        db.query(Milestone)
        .filter(
            Milestone.contract_id == milestone.contract_id,
            Milestone.order_index < milestone.order_index,
            Milestone.status == "released",
        )
        .count()
    )
    return released == previous


def finalize_milestone_release(db: Session, contract: Contract, milestone: Milestone, autopilot: bool = False) -> None:
    """Shared completion logic: mark milestone released, auto-complete the contract
    when every milestone is released, notify both parties, fire the n8n event.

    Called from two paths: (1) the instant demo-release button below, and
    (2) the real Stripe webhook once a checkout payment actually settles
    (see routes/payments.py + routes/webhooks.py) — money now genuinely moves
    when Stripe is configured, closing the platform's biggest functional gap.
    """
    milestone.status = "released"
    milestone.released_at = datetime.now(timezone.utc)
    db.commit()

    remaining = (
        db.query(Milestone)
        .filter(Milestone.contract_id == contract.id, Milestone.status != "released")
        .count()
    )
    if remaining == 0:
        contract.status = "completed"
        contract.completed_at = datetime.now(timezone.utc)
        job = db.get(Job, contract.job_id)
        if job:
            job.status = "completed"
        create_notification(
            db,
            contract.client_id,
            "Contract completed 🎉",
            "All milestones released. Thank you for using DROPIFY!",
            "success",
        )
        create_notification(
            db,
            contract.freelancer_id,
            "Contract completed 🎉",
            f"All milestones released — {contract.amount:.2f} PLN (minus fee) will be paid out.",
            "success",
        )
        db.commit()

    notify_n8n("milestone-released", {
        "contract_id": contract.id,
        "milestone_id": milestone.id,
        "amount": milestone.amount,
        "autopilot": autopilot,
        "contract_completed": remaining == 0,
    })


def _release(db: Session, contract: Contract, milestone: Milestone, autopilot: bool = False) -> Payment:
    """Instant/demo release path used when Stripe isn't configured — keeps the
    platform 'self-working' out of the box (same fallback philosophy as the AI
    utilities). When STRIPE_SECRET_KEY is set, real payment collection goes
    through POST /api/payments/checkout/{contract_id}/{milestone_id} instead."""
    freelancer = db.get(User, contract.freelancer_id)
    fee = round(milestone.amount * (contract.fee_rate or 0.08), 2)
    payment = Payment(
        contract_id=contract.id,
        milestone_id=milestone.id,
        amount=round(milestone.amount, 2),
        platform_fee=fee,
        net_amount=round(milestone.amount - fee, 2),
        status="paid",
        provider="demo",
        payout_method=freelancer.payout_method if freelancer else "bank",
        payout_address=freelancer.payout_address if freelancer else None,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    finalize_milestone_release(db, contract, milestone, autopilot=autopilot)
    return payment
