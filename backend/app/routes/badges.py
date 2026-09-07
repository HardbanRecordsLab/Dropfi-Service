"""#17 Skill Badges routes: list available badges, user badges, portfolio stats."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import ORMModel
from app.utils.badges import get_available_badges, get_user_badges, get_portfolio_stats


router = APIRouter(prefix="/badges", tags=["Skill Badges"])


class BadgeOut(ORMModel):
    id: str
    badge_key: str
    name: str
    score: int
    level: str
    verified_at: str | None


class PortfolioStatsOut(ORMModel):
    total_badges: int
    gold: int
    silver: int
    bronze: int
    average_score: float
    verified: bool


@router.get("")
def list_badges():
    """List all available badge types."""
    return get_available_badges()


@router.get("/mine", response_model=list[BadgeOut])
def my_badges(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get badges earned by the current user."""
    return get_user_badges(db, user.id)


@router.get("/user/{user_id}", response_model=list[BadgeOut])
def user_badges(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get public badges for any user (portfolio view)."""
    return get_user_badges(db, user_id)


@router.get("/stats", response_model=PortfolioStatsOut)
def my_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get portfolio stats for the current user."""
    return get_portfolio_stats(db, user.id)


@router.get("/stats/{user_id}", response_model=PortfolioStatsOut)
def user_stats(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get public portfolio stats for any user."""
    return get_portfolio_stats(db, user_id)
