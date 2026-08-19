import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Payment, Contract, Milestone
from app.config import settings

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = logging.getLogger(__name__)


@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Stripe webhook: confirms real Checkout/PaymentIntent settlement and
    finalizes the milestone release (mirrors the instant demo-release path in
    routes/contracts.py, but only fires once money has genuinely moved)."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = payload.get("type", "")
    obj = payload.get("data", {}).get("object", {})

    if event_type in ("checkout.session.completed", "payment_intent.succeeded"):
        metadata = obj.get("metadata", {})
        contract_id = metadata.get("contract_id")
        payment_id = metadata.get("payment_id")
        milestone_id = metadata.get("milestone_id")

        payment = db.get(Payment, payment_id) if payment_id else None
        if payment and payment.status != "paid":
            payment.status = "paid"
            payment.provider_ref = obj.get("id", "")
            db.commit()

            contract = db.get(Contract, payment.contract_id)
            milestone = db.get(Milestone, milestone_id or payment.milestone_id)
            if contract and milestone and milestone.status != "released":
                from app.routes.contracts import finalize_milestone_release
                finalize_milestone_release(db, contract, milestone)
            return {"received": True}

        if contract_id and not payment_id:
            # Legacy/manual flow: no pre-created Payment row — record it directly.
            contract = db.get(Contract, contract_id)
            if contract:
                payment = Payment(
                    contract_id=contract.id,
                    amount=contract.amount,
                    platform_fee=contract.platform_fee,
                    net_amount=round(contract.amount - contract.platform_fee, 2),
                    status="paid",
                    provider="stripe",
                    provider_ref=obj.get("id", ""),
                )
                db.add(payment)
                db.commit()
                return {"received": True}

    return {"received": True, "status": "ignored"}


@router.get("/health")
def webhook_health():
    return {"status": "ok", "stripe": bool(settings.STRIPE_WEBHOOK_SECRET)}
