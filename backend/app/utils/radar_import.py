"""Turn Portal Radar leads into live DROPIFY jobs.

- Budgets are converted to PLN (connectors keep non-PLN amounts only in
  ``budget_text`` + ``currency``; the old import used a flat 500 PLN for them).
- ``top_up_open_jobs`` keeps the marketplace at a minimum number of open jobs,
  preferring project-type sources (freelance gigs) over full-time job boards,
  freshest and best-fitting first.
- ``expire_stale_imports`` closes imported jobs whose source posting is old,
  so the board doesn't fill with dead leads.

Imported jobs carry ``external_source``; matching treats them as leads: in-app
notification only (no e-mail) and no Autopilot contract with the bot account.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.models import ExternalListing, Job, Match, User
from app.utils.currency import _fetch_live_rates
from app.utils.jobs import create_job_and_match
from app.utils.security import hash_password, make_referral_code

logger = logging.getLogger(__name__)

# Gig/project sources first — they match a freelance marketplace; job boards fill the rest.
SOURCE_PRIORITY = [
    "freelancer", "freelancehunt", "wpzlecenia", "useme",
    "weworkremotely", "remoteok", "remotive", "jobicy", "arbeitnow", "hn_hiring",
]
DEFAULT_BUDGET_PLN = 500.0
MIN_BUDGET_PLN = 50.0
_SYMBOLS = {"€": "EUR", "£": "GBP", "₹": "INR", "₴": "UAH", "zł": "PLN", "$": "USD"}
_NUM_RE = re.compile(r"\d[\d\s.,]*")


def radar_bot(db: Session) -> User:
    """The client account that owns jobs imported from external leads."""
    bot = db.query(User).filter(User.email == settings.RADAR_BOT_EMAIL).first()
    if bot is None:
        import secrets
        bot = User(
            email=settings.RADAR_BOT_EMAIL,
            password_hash=hash_password(secrets.token_urlsafe(24)),
            role="client",
            first_name="Portal",
            last_name="Radar",
            company="DROPIFY Portal Radar",
            is_active=True,
            referral_code=make_referral_code(settings.RADAR_BOT_EMAIL),
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)
    return bot


def _parse_amount(token: str) -> float | None:
    t = token.strip().replace(" ", "").replace(" ", "")
    if "," in t and "." in t:
        t = t.replace(",", "")
    elif t.count(",") == 1 and len(t.split(",")[1]) <= 2:
        t = t.replace(",", ".")
    else:
        t = t.replace(",", "")
    try:
        return float(t)
    except ValueError:
        return None


def budget_to_pln(row: ExternalListing) -> tuple[float, bool]:
    """Return (budget in PLN, known). `known=False` means a default was used."""
    if row.budget_max or row.budget_min:  # connectors only fill these when already PLN
        return float(row.budget_max or row.budget_min), True
    text = row.budget_text or ""
    amounts = [a for a in (_parse_amount(m.group(0)) for m in _NUM_RE.finditer(text)) if a]
    if not amounts:
        return DEFAULT_BUDGET_PLN, False
    code = (row.currency or "").upper()
    if not code:
        code = next((c for sym, c in _SYMBOLS.items() if sym in text), "USD")
    rates, _ = _fetch_live_rates()
    rate = (rates or {}).get(code)  # 1 PLN = rate * CUR
    if not rate:
        return DEFAULT_BUDGET_PLN, False
    lo, hi = min(amounts), max(amounts)
    # Freelancer.com allows junk ranges like "$10 - $100000"; above a 10x spread,
    # take a realistic point near the low end instead of the ceiling.
    amount = hi if hi <= lo * 10 else min(hi, lo * 3)
    pln = amount / rate
    return round(max(pln, MIN_BUDGET_PLN), 0), True


def import_listing_row(db: Session, row: ExternalListing, bot: User | None = None) -> Job:
    bot = bot or radar_bot(db)
    budget, known = budget_to_pln(row)
    budget_line = (
        f"Budżet źródłowy / Source budget: {row.budget_text} (≈ {budget:.0f} PLN)" if row.budget_text and known
        else "Budżet do uzgodnienia / Budget to be agreed" if not known else ""
    )
    description = (
        f"{(row.description or row.title).strip()}\n\n"
        f"---\nŹródło / Source: {row.source} — {row.url}\n"
        f"Firma / Company: {row.company or 'n/a'}\n"
        f"Lokalizacja / Location: {row.location or ('Remote' if row.is_remote else 'n/a')}"
        + (f"\n{budget_line}" if budget_line else "")
        + (f"\nKontakt / Contact: {row.contact}" if row.contact else "")
    )
    job = create_job_and_match(
        db,
        title=row.title,
        description=description[:20000],
        budget=float(budget),
        deadline=date.today() + timedelta(days=14),
        location=row.location or ("Remote" if row.is_remote else ""),
        category=row.category or "",
        required_skills=[t for t in (row.tags or []) if isinstance(t, str)][:8],
        client_id=bot.id,
        source=f"radar:{row.source}",
        external_source=row.source,
        external_url=row.url,
    )
    row.status = "imported"
    row.imported_job_id = job.id
    db.commit()
    return job


def _candidates(db: Session, max_age_days: int, min_fit: float):
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    disabled = {s.strip() for s in settings.RADAR_DISABLED_SOURCES.split(",") if s.strip()}
    q = (
        db.query(ExternalListing)
        .filter(ExternalListing.status == "new", ExternalListing.imported_job_id.is_(None))
        .filter(or_(ExternalListing.posted_at.is_(None) & (ExternalListing.fetched_at >= cutoff),
                    ExternalListing.posted_at >= cutoff))
        .filter(func.length(ExternalListing.description) >= 60)
    )
    if min_fit > 0:
        q = q.filter(ExternalListing.fit_score >= min_fit)
    for source in SOURCE_PRIORITY + ["*"]:
        if source in disabled:
            continue
        sq = q.filter(~ExternalListing.source.in_(SOURCE_PRIORITY)) if source == "*" else q.filter(ExternalListing.source == source)
        for row in sq.order_by(ExternalListing.fit_score.desc().nullslast(), ExternalListing.posted_at.desc().nullslast()).limit(2000).all():
            yield row


def open_jobs_count(db: Session) -> int:
    return db.query(func.count(Job.id)).filter(Job.status.in_(["open", "matched"])).scalar() or 0


def top_up_open_jobs(db: Session, target: int | None = None, max_age_days: int | None = None,
                     min_fit: float = 0, max_import: int = 300) -> dict:
    """Import fresh leads until at least `target` jobs are open."""
    target = settings.RADAR_MIN_OPEN_JOBS if target is None else target
    max_age_days = max_age_days or settings.RADAR_IMPORT_MAX_AGE_DAYS
    before = open_jobs_count(db)
    need = max(0, target - before)
    imported, failed, by_source, seen_titles = 0, 0, {}, set()
    if need:
        bot = radar_bot(db)
        seen_titles = {t.lower() for (t,) in db.query(Job.title).filter(Job.client_id == bot.id,
                                                                        Job.status.in_(["open", "matched"])).all()}
        for row in _candidates(db, max_age_days, min_fit):
            if imported >= min(need, max_import):
                break
            key = (row.title or "").strip().lower()
            if not key or key in seen_titles:  # same gig reposted / cross-posted
                continue
            try:
                import_listing_row(db, row, bot)
                seen_titles.add(key)
                imported += 1
                by_source[row.source] = by_source.get(row.source, 0) + 1
            except Exception:  # noqa: BLE001 — one bad lead must not stop the batch
                logger.exception("Radar import failed for listing %s", row.id)
                db.rollback()
                failed += 1
    return {"open_before": before, "target": target, "imported": imported, "failed": failed,
            "by_source": by_source, "open_after": open_jobs_count(db)}


def expire_stale_imports(db: Session, max_age_days: int | None = None) -> int:
    """Close imported leads nobody engaged with once they pass their age limit."""
    max_age_days = max_age_days or settings.RADAR_IMPORT_MAX_AGE_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    stale = (
        db.query(Job)
        .filter(Job.external_source.isnot(None), Job.status.in_(["open", "matched"]), Job.created_at < cutoff)
        .all()
    )
    closed = 0
    for job in stale:
        if db.query(Match).filter(Match.job_id == job.id, Match.status == "accepted").first():
            continue
        job.status = "cancelled"
        closed += 1
    db.commit()
    return closed
