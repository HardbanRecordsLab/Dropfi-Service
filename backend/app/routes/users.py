from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import User, Rating, Contract
from app.schemas import UserUpdate, UserOut, FreelancerOut
from app.utils.ai import embed_text, freelancer_search_text
from app.utils.security import make_referral_code

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me/profile", response_model=UserOut)
def my_profile(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserOut)
def update_profile(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    if user.role == "freelancer":
        search_text = freelancer_search_text(user)
        embedding = embed_text(search_text)
        user.embedding_json = str(embedding)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=FreelancerOut)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}/risk-score")
def user_risk_score(user_id: str, db: Session = Depends(get_db)):
    """#F4 Smart Supplier Risk Score: explainable 0-100 trust score."""
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    from app.utils.risk import calculate_risk_score
    return calculate_risk_score(target)


@router.get("", response_model=list[FreelancerOut])
def list_freelancers(
    search: str = "",
    skill: str = "",
    location: str = "",
    db: Session = Depends(get_db),
):
    q = db.query(User).filter(User.role == "freelancer", User.is_active == True)
    if search:
        like = f"%{search.lower()}%"
        q = q.filter(User.email.like(like) | User.bio.like(like) | User.first_name.like(like) | User.last_name.like(like))
    if skill:
        q = q.filter(User.skills.icontains(skill))
    if location:
        q = q.filter(User.location.ilike(f"%{location}%"))
    return q.order_by(User.rating.desc()).limit(100).all()
