"""Real payment collection (closes the platform's biggest functional gap:
previously every 'release payment' just wrote a Payment(status='paid') row
without any money ever actually moving). When STRIPE_SECRET_KEY is configured,
this creates a genuine Stripe Checkout Session; the webhook in webhooks.py
confirms settlement and finalizes the milestone release. Without a Stripe key
the platform keeps working via the existing instant demo-release button on
POST /contracts/{id}/milestones/{id}/release — same fallback philosophy as
the AI features elsewhere in this codebase.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, Contract, Milestone, Payment
from app.config import settings

router = APIRouter(prefix="/payments", tags=["Payments"])
logger = logging.getLogger(__name__)


@router.get("/config")
def payments_config():
    return {
        "stripe_enabled": bool(settings.STRIPE_SECRET_KEY),
        "publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
    }


@router.post("/checkout/{contract_id}/{milestone_id}")
def create_checkout(
    contract_id: str,
    milestone_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.client_id != user.id:
        raise HTTPException(status_code=403, detail="Only the client can pay")
    milestone = db.get(Milestone, milestone_id)
    if not milestone or milestone.contract_id != contract.id:
        raise HTTPException(status_code=404, detail="Milestone not found")
    if milestone.status != "in_review":
        raise HTTPException(status_code=400, detail="Milestone must be submitted and in review before payment")

    already_paid = (
        db.query(Payment)
        .filter(Payment.milestone_id == milestone.id, Payment.status.in_(["paid", "pending"]))
        .first()
    )
    if already_paid:
        raise HTTPException(status_code=400, detail="A payment for this milestone already exists")

    if not settings.STRIPE_SECRET_KEY:
        return {
            "mode": "demo",
            "message": "Stripe is not configured on this server — use 'Release payment' to settle in demo mode.",
        }

    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        freelancer = db.get(User, contract.freelancer_id)
        fee = round(milestone.amount * (contract.fee_rate or 0.08), 2)
        payment = Payment(
            contract_id=contract.id,
            milestone_id=milestone.id,
            amount=round(milestone.amount, 2),
            platform_fee=fee,
            net_amount=round(milestone.amount - fee, 2),
            status="pending",
            provider="stripe",
            payout_method=freelancer.payout_method if freelancer else "bank",
            payout_address=freelancer.payout_address if freelancer else None,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "pln",
                    "product_data": {"name": f"DROPIFY milestone: {milestone.title}"},
                    "unit_amount": int(round(milestone.amount * 100)),
                },
                "quantity": 1,
            }],
            metadata={
                "contract_id": contract.id,
                "payment_id": payment.id,
                "milestone_id": milestone.id,
            },
            success_url=f"{settings.FRONTEND_URL}/dashboard/contracts?paid=1",
            cancel_url=f"{settings.FRONTEND_URL}/dashboard/contracts?cancelled=1",
        )
        return {"mode": "stripe", "checkout_url": session.url, "payment_id": payment.id}
    except Exception as exc:
        logger.warning("Stripe checkout failed (%s)", exc)
        raise HTTPException(status_code=502, detail="Payment provider error — please try again shortly")
