"""#F7 Global Talent Time-Zone Auto-Scheduler.

Suggests overlap windows between a client and a freelancer so a marketplace
built for global (not just Polish) reach can route work across regions
without manual back-and-forth — including near-24/7 async handoff pairings.
"""

# Best-effort UTC offsets keyed by free-text location/country keywords, matching
# the existing `location`/`country` string fields used across the app.
UTC_OFFSETS = {
    "poland": 1, "polska": 1, "warsaw": 1, "warszawa": 1, "krakow": 1, "cracow": 1, "gdansk": 1,
    "germany": 1, "niemcy": 1, "france": 1, "spain": 1, "hiszpania": 1, "italy": 1, "wlochy": 1,
    "uk": 0, "united kingdom": 0, "london": 0, "portugal": 0,
    "ukraine": 2, "ukraina": 2, "kyiv": 2, "kiev": 2, "romania": 2, "greece": 2,
    "usa": -5, "united states": -5, "new york": -5, "chicago": -6, "los angeles": -8, "california": -8,
    "india": 5.5, "indie": 5.5, "mumbai": 5.5, "delhi": 5.5,
    "philippines": 8, "manila": 8, "singapore": 8, "china": 8,
    "japan": 9, "tokyo": 9, "australia": 10, "sydney": 10,
    "brazil": -3, "brazylia": -3, "sao paulo": -3,
    "uae": 4, "dubai": 4, "united arab emirates": 4,
}
DEFAULT_OFFSET = 1.0  # assume CET (platform's home base) when unknown


def guess_offset(location: str, country: str = "") -> float:
    blob = f"{location} {country}".lower()
    for key, offset in UTC_OFFSETS.items():
        if key in blob:
            return float(offset)
    return DEFAULT_OFFSET


def _overlap_hours(offset_a: float, offset_b: float, work_start: int = 9, work_end: int = 18) -> tuple[float, list[float] | None]:
    start_a, end_a = work_start - offset_a, work_end - offset_a
    start_b, end_b = work_start - offset_b, work_end - offset_b
    lo, hi = max(start_a, start_b), min(end_a, end_b)
    hours = max(0.0, hi - lo)
    if hours <= 0:
        return 0.0, None
    return round(hours, 1), [round(lo % 24, 1), round(hi % 24, 1)]


def schedule_suggestion(client_location: str, client_country: str, freelancer_location: str, freelancer_country: str) -> dict:
    offset_a = guess_offset(client_location, client_country)
    offset_b = guess_offset(freelancer_location, freelancer_country)
    hours_apart = round(abs(offset_a - offset_b), 1)
    overlap_hours, utc_window = _overlap_hours(offset_a, offset_b)

    if overlap_hours >= 3:
        mode, tip = "live-overlap", "Enough working-hours overlap for live back-and-forth communication."
    elif overlap_hours > 0:
        mode, tip = "handoff", "Small overlap — plan a short daily sync inside the shared window, async the rest."
    else:
        mode, tip = "async-24-7", "No live overlap — this pairing gives near 24/7 turnaround via async handoff."

    return {
        "client_utc_offset": offset_a,
        "freelancer_utc_offset": offset_b,
        "hours_apart": hours_apart,
        "overlap_hours": overlap_hours,
        "suggested_utc_window": utc_window,
        "mode": mode,
        "tip": tip,
    }
