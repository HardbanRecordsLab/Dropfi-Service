from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import User, Commission, Referral

router = APIRouter(prefix="/referrals", tags=["Referrals"])


@router.get("/me", response_model=dict)
def my_referrals(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    commissions = (
        db.query(Commission)
        .filter(Commission.referrer_id == user.id)
        .order_by(Commission.created_at.desc())
        .limit(100)
        .all()
    )
    total_earned = sum(c.amount for c in commissions if c.status == "paid")
    pending = sum(c.amount for c in commissions if c.status == "pending")
    referred_count = db.query(func.count(Referral.id)).filter(Referral.referrer_id == user.id).scalar() or 0

    return {
        "referral_code": user.referral_code,
        "total_earned": round(total_earned, 2),
        "pending": round(pending, 2),
        "referred_count": referred_count,
        "rate_l1": settings.REFERRAL_RATE_L1,
        "rate_l2": settings.REFERRAL_RATE_L2,
        "window_months": settings.REFERRAL_MONTHS,
        "commissions": [
            {
                "id": c.id,
                "level": c.level,
                "rate": c.rate,
                "amount": c.amount,
                "status": c.status,
                "contract_id": c.contract_id,
                "referred_name": (c.referred.first_name + " " + c.referred.last_name).strip() if c.referred else "",
                "created_at": str(c.created_at),
            }
            for c in commissions
        ],
    }
