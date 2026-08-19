from datetime import date, datetime


def calculate_match_score(
    semantic: float,
    rating: float,
    budget: float,
    fair_price: float,
    deadline: date,
) -> float:
    """SCORE = (Semantic * 0.40) + (Rating * 0.25) + (Price_Fit * 0.20) + (Availability * 0.15)"""
    semantic_score = max(0.0, min(1.0, semantic))

    rating_score = rating / 5.0 if rating else 0.70
    rating_score = max(0.0, min(1.0, rating_score))

    if budget >= fair_price * 0.8:
        price_fit = 1.0
    elif budget >= fair_price * 0.5:
        price_fit = 0.5
    else:
        price_fit = 0.2

    days_left = (deadline - datetime.utcnow().date()).days
    if days_left >= 7:
        availability = 1.0
    elif days_left >= 3:
        availability = 0.7
    else:
        availability = 0.3

    score = (
        semantic_score * 0.40
        + rating_score * 0.25
        + price_fit * 0.20
        + availability * 0.15
    )
    return round(score, 4)
