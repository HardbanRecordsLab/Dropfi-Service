"""#17 Skill Badges + AI-Verified Portfolio.

Freelancers earn badges by completing AI-verified skill assessments.
Each badge has a category, difficulty level, and an AI-generated score.
"""

from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import User, Badge


# Badge definitions — each maps to a skill category
BADGE_DEFINITIONS = {
    "photography": {
        "name": "Photography Expert",
        "name_pl": "Ekspert fotografii",
        "description": "AI-verified photography skills assessment",
        "category": "visual",
        "icon": "camera",
    },
    "copywriting": {
        "name": "Copywriting Pro",
        "name_pl": "Profesjonalista copywritingu",
        "description": "AI-verified copywriting and SEO skills",
        "category": "content",
        "icon": "pen",
    },
    "video_editing": {
        "name": "Video Editor",
        "name_pl": "Edytor wideo",
        "description": "AI-verified video editing and production skills",
        "category": "visual",
        "icon": "film",
    },
    "graphic_design": {
        "name": "Graphic Designer",
        "name_pl": "Grafik",
        "description": "AI-verified graphic design and branding skills",
        "category": "visual",
        "icon": "palette",
    },
    "web_development": {
        "name": "Web Developer",
        "name_pl": "Programista web",
        "description": "AI-verified web development skills",
        "category": "technical",
        "icon": "code",
    },
    "ecommerce": {
        "name": "E-commerce Specialist",
        "name_pl": "Specjalista e-commerce",
        "description": "AI-verified e-commerce and dropshipping knowledge",
        "category": "business",
        "icon": "shop",
    },
    "seo": {
        "name": "SEO Expert",
        "name_pl": "Ekspert SEO",
        "description": "AI-verified SEO and analytics skills",
        "category": "marketing",
        "icon": "search",
    },
    "translation": {
        "name": "Translator",
        "name_pl": "Tłumacz",
        "description": "AI-verified translation and localization skills",
        "category": "content",
        "icon": "globe",
    },
}


def get_available_badges() -> list[dict]:
    """Return all available badge types with their definitions."""
    return [
        {"key": key, **defn}
        for key, defn in BADGE_DEFINITIONS.items()
    ]


def get_user_badges(db: Session, user_id: str) -> list[dict]:
    """Return all badges earned by a user."""
    badges = db.query(Badge).filter(Badge.user_id == user_id).all()
    return [
        {
            "id": b.id,
            "badge_key": b.badge_key,
            "name": BADGE_DEFINITIONS.get(b.badge_key, {}).get("name", b.badge_key),
            "score": b.score,
            "level": b.level,
            "verified_at": b.verified_at.isoformat() if b.verified_at else None,
        }
        for b in badges
    ]


def award_badge(
    db: Session,
    user_id: str,
    badge_key: str,
    score: int,
) -> Badge | None:
    """Award a badge to a user if they don't already have it or if the new score is higher."""
    if badge_key not in BADGE_DEFINITIONS:
        return None

    existing = (
        db.query(Badge)
        .filter(Badge.user_id == user_id, Badge.badge_key == badge_key)
        .first()
    )

    # Determine level from score
    if score >= 90:
        level = "gold"
    elif score >= 70:
        level = "silver"
    else:
        level = "bronze"

    if existing:
        if score > existing.score:
            existing.score = score
            existing.level = level
            db.commit()
            db.refresh(existing)
        return existing

    badge = Badge(
        user_id=user_id,
        badge_key=badge_key,
        score=score,
        level=level,
    )
    db.add(badge)
    db.commit()
    db.refresh(badge)
    return badge


def get_portfolio_stats(db: Session, user_id: str) -> dict:
    """Get portfolio statistics for a user's badge collection."""
    badges = db.query(Badge).filter(Badge.user_id == user_id).all()
    total = len(badges)
    gold = sum(1 for b in badges if b.level == "gold")
    silver = sum(1 for b in badges if b.level == "silver")
    bronze = sum(1 for b in badges if b.level == "bronze")
    avg_score = round(sum(b.score for b in badges) / total, 1) if total > 0 else 0

    return {
        "total_badges": total,
        "gold": gold,
        "silver": silver,
        "bronze": bronze,
        "average_score": avg_score,
        "verified": total > 0,
    }
