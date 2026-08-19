"""#F4 Smart Supplier Risk Score.

Lightweight, fully explainable risk/trust scoring for freelancers & suppliers
using data already on the platform (rating, track record, completion rate) —
no external credit bureau, no black box.
"""


def calculate_risk_score(user) -> dict:
    """0-100, higher = lower risk / more trustworthy."""
    rating_component = (user.rating or 0) / 5.0 * 40  # 0-40
    volume_component = min(user.completed_jobs or 0, 20) / 20 * 25  # 0-25

    completion_rate = 1.0
    if (user.total_jobs or 0) > 0:
        completion_rate = min(1.0, (user.completed_jobs or 0) / user.total_jobs)
    reliability_component = completion_rate * 25  # 0-25

    reviews_component = min(user.rating_count or 0, 10) / 10 * 10  # 0-10

    score = round(max(0.0, min(100.0, rating_component + volume_component + reliability_component + reviews_component)), 1)

    if score >= 75:
        level, label = "low", "Low risk"
    elif score >= 45:
        level, label = "medium", "Medium risk"
    else:
        level, label = "high", "New / unverified"

    return {
        "score": score,
        "level": level,
        "label": label,
        "factors": {
            "rating": round(rating_component, 1),
            "track_record": round(volume_component, 1),
            "completion_rate": round(reliability_component, 1),
            "review_volume": round(reviews_component, 1),
        },
    }
