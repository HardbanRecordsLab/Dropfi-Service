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
    """Stripe webhook: verifies the event signature, confirms real Checkout/
    PaymentIntent settlement, and finalizes the milestone release (mirrors the
    instant demo-release path in routes/contracts.py, but only fires once
    money has genuinely moved).

    SECURITY: without signature verification, anyone who knows this URL could
    POST a forged 'checkout.session.completed' body and mark any pending
    payment as paid without ever paying. STRIPE_WEBHOOK_SECRET is therefore
    required whenever this endpoint is used for real (Stripe-side) traffic —
    requests are rejected outright if it isn't configured.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe webhooks are not configured on this server")

    raw_body = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        import stripe
        event = stripe.Webhook.construct_event(raw_body, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as exc:
        logger.warning("Stripe webhook signature verification failed (%s)", exc)
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event.get("type", "")
    obj = event.get("data", {}).get("object", {})

    if event_type in ("checkout.session.completed", "payment_intent.succeeded"):
        metadata = obj.get("metadata", {})
        contract_id = metadata.get("contract_id")
        payment_id = metadata.get("payment_id")
        milestone_id = metadata.get("milestone_id")
        # checkout.session carries `payment_intent`; payment_intent.succeeded IS the PI (its own `id`).
        # Stored as provider_ref so a later refund (routes/payments.py::refund_stripe_payment) can
        # target the actual charge instead of the (unrefundable) Checkout Session id.
        payment_intent_ref = obj.get("payment_intent") or obj.get("id", "")

        payment = db.get(Payment, payment_id) if payment_id else None
        if payment and payment.status != "paid":
            payment.status = "paid"
            payment.provider_ref = payment_intent_ref
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
                    provider_ref=payment_intent_ref,
                )
                db.add(payment)
                db.commit()
                return {"received": True}

    return {"received": True, "status": "ignored"}


@router.get("/health")
def webhook_health():
    return {"status": "ok", "stripe": bool(settings.STRIPE_WEBHOOK_SECRET)}
