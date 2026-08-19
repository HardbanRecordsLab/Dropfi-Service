"""Risk-based platform fee calculation (feature #8)."""
from app.config import settings


def calculate_fee_rate(freelancer) -> float:
    """Top-rated freelancers pay 5%, new pay 12%, everyone else 8%."""
    if (
        freelancer.rating_count >= settings.TOP_RATING_COUNT_MIN
        and freelancer.rating >= settings.TOP_RATING_MIN
    ):
        return settings.FEE_RATE_TOP
    if freelancer.rating_count <= settings.NEW_RATING_COUNT_MAX:
        return settings.FEE_RATE_NEW
    return settings.PLATFORM_FEE_RATE


def fee_rate_tiers() -> dict:
    return {
        "top": settings.FEE_RATE_TOP,
        "default": settings.PLATFORM_FEE_RATE,
        "new": settings.FEE_RATE_NEW,
        "top_rating_min": settings.TOP_RATING_MIN,
        "top_rating_count_min": settings.TOP_RATING_COUNT_MIN,
        "new_rating_count_max": settings.NEW_RATING_COUNT_MAX,
    }
