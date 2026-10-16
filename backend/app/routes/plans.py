import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import User, Subscription

router = APIRouter(prefix="/plans", tags=["Plans"])
logger = logging.getLogger(__name__)

PLANS = {
    "free": {"price": 0, "jobs_per_month": 5, "features": ["5 jobs/month", "Basic AI matching"]},
    "starter": {"price": 49, "jobs_per_month": 50, "features": ["50 jobs/month", "Analytics", "Email support"]},
    "pro": {"price": 149, "jobs_per_month": 0, "features": ["Unlimited jobs", "Priority matching", "AI tuning", "Slack support"]},
    "enterprise": {"price": 499, "jobs_per_month": 0, "features": ["Custom rules", "Dedicated manager", "API v2", "SLA"]},
}


@router.get("", response_model=dict)
def list_plans():
    return PLANS


@router.post("/subscribe", response_model=dict)
def subscribe(
    plan: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if plan not in PLANS:
        raise HTTPException(status_code=400, detail="Unknown plan")
    if plan == "free":
        user.plan = "free"
        db.commit()
        return {"plan": "free", "price": 0, "message": "Downgraded to free"}

    if settings.STRIPE_SECRET_KEY:
        # Paid plans are activated by the Stripe webhook once the payment settles.
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.create(
                mode="payment",
                customer_email=user.email,
                line_items=[{
                    "price_data": {
                        "currency": "pln",
                        "product_data": {"name": f"DROPIFY {plan.capitalize()} — 30 days"},
                        "unit_amount": int(PLANS[plan]["price"] * 100),
                    },
                    "quantity": 1,
                }],
                metadata={"kind": "plan", "plan": plan, "user_id": user.id},
                success_url=f"{settings.FRONTEND_URL}/profile?plan=1",
                cancel_url=f"{settings.FRONTEND_URL}/profile?plan_cancelled=1",
            )
        except Exception as exc:
            logger.warning("Stripe plan checkout failed (%s)", exc)
            raise HTTPException(status_code=502, detail="Payment provider error — please try again shortly")
        return {"plan": plan, "price": PLANS[plan]["price"], "mode": "stripe", "checkout_url": session.url}

    # Demo mode (no Stripe key): activate instantly so the platform stays self-working.
    activate_plan(db, user.id, plan)
    return {"plan": plan, "price": PLANS[plan]["price"], "mode": "demo", "message": "Subscription updated"}


def activate_plan(db: Session, user_id: str, plan: str, provider_ref: str = "") -> bool:
    user = db.get(User, user_id)
    if not user or plan not in PLANS or plan == "free":
        logger.warning("activate_plan: bad user/plan (%s, %s) ref=%s", user_id, plan, provider_ref)
        return False
    active = db.query(Subscription).filter(Subscription.user_id == user.id, Subscription.status == "active").first()
    if active:
        active.plan = plan
        active.price = PLANS[plan]["price"]
        active.renews_at = date.today() + timedelta(days=30)
    else:
        db.add(Subscription(
            user_id=user.id,
            plan=plan,
            price=PLANS[plan]["price"],
            renews_at=date.today() + timedelta(days=30),
        ))
    user.plan = plan
    db.commit()
    return True
