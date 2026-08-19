from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, Subscription

router = APIRouter(prefix="/plans", tags=["Plans"])

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
    return {"plan": plan, "price": PLANS[plan]["price"], "message": "Subscription updated"}
