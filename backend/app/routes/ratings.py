from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, Rating, Contract
from app.schemas import RatingCreate, RatingOut

router = APIRouter(prefix="/ratings", tags=["Ratings"])


@router.post("", response_model=RatingOut, status_code=201)
def create_rating(
    data: RatingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.to_user_id == user.id:
        raise HTTPException(status_code=400, detail="You cannot rate yourself")

    target = db.get(User, data.to_user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Rated user not found")

    if data.job_id:
        contract = (
            db.query(Contract)
            .filter(Contract.job_id == data.job_id)
            .first()
        )
        if not contract:
            raise HTTPException(status_code=400, detail="No contract for this job")
        if contract.client_id != user.id and contract.freelancer_id != user.id:
            raise HTTPException(status_code=403, detail="You were not part of this job")
        existing = (
            db.query(Rating)
            .filter(Rating.from_user_id == user.id, Rating.to_user_id == data.to_user_id, Rating.job_id == data.job_id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="You already rated this job")

    rating = Rating(
        from_user_id=user.id,
        to_user_id=data.to_user_id,
        job_id=data.job_id,
        score=data.score,
        comment=data.comment,
    )
    db.add(rating)
    db.commit()

    all_ratings = db.query(Rating).filter(Rating.to_user_id == target.id).all()
    if all_ratings:
        avg = sum(r.score for r in all_ratings) / len(all_ratings)
        target.rating = round(avg, 2)
        target.rating_count = len(all_ratings)
    db.commit()
    db.refresh(rating)
    return rating


@router.get("/user/{user_id}", response_model=list[RatingOut])
def user_ratings(user_id: str, db: Session = Depends(get_db)):
    ratings = (
        db.query(Rating)
        .filter(Rating.to_user_id == user_id)
        .order_by(Rating.created_at.desc())
        .all()
    )
    out = []
    for r in ratings:
        item = RatingOut.model_validate(r)
        item.from_user = db.get(User, r.from_user_id)
        out.append(item)
    return out
