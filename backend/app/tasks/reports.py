"""Automation reports: daily AI summary, referral commissions, auto-completion of overdue jobs."""
import logging
from datetime import datetime, timedelta, date

from celery import shared_task
from sqlalchemy import func

from app.config import settings
from app.database import SessionLocal
from app.models import (
    User, Job, Match, Contract, Payment, Notification, Commission, DailyReport, Milestone,
)
from app.utils.ai import generate_daily_insights
from app.utils.emailer import notify_email
from app.utils.notifications import create_notification
from app.utils.n8n import notify_n8n

logger = logging.getLogger(__name__)


def _compute_anomalies(metrics: dict, db) -> list[str]:
    anomalies = []
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    # 1. Revenue trend vs 7-day average
    prev_revenue = (
        db.query(func.coalesce(func.sum(Payment.platform_fee), 0))
        .filter(Payment.created_at >= week_ago, Payment.created_at < yesterday, Payment.status == "paid")
        .scalar()
        or 0
    )
    daily_avg = prev_revenue / 7.0
    revenue = metrics.get("revenue", 0)
    if daily_avg > 0 and revenue < daily_avg * 0.5:
        anomalies.append(
            f"Revenue drop: today {revenue:.2f} PLN vs 7-day avg {daily_avg:.2f} PLN ({(1 - revenue / daily_avg) * 100:.0f}% below)"
        )

    # 2. Match acceptance conversion
    matches = metrics.get("matches", 0)
    accepted = metrics.get("accepted", 0)
    if matches > 5 and accepted / matches < 0.2:
        anomalies.append(f"Low match acceptance: {accepted / matches:.0%} (target > 20%) — check match quality")

    # 3. Errors
    if metrics.get("errors", 0) > 3:
        anomalies.append(f"Elevated errors: {metrics['errors']} in 24h — check logs")

    # 4. Signups
    if metrics.get("new_users", 0) == 0:
        anomalies.append("No new signups in 24h — consider referral push")

    # 5. Pending matches aging
    stale = (
        db.query(func.count(Match.id))
        .filter(Match.status == "pending", Match.created_at < now - timedelta(days=3))
        .scalar()
        or 0
    )
    if stale > 5:
        anomalies.append(f"{stale} matches pending over 3 days — freelancers may be ignoring them")

    return anomalies


@shared_task(name="app.tasks.reports.daily_summary")
def daily_summary():
    if not settings.DAILY_SUMMARY_ENABLED:
        return {"disabled": True}
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        today = date.today()

        jobs_today = db.query(func.count(Job.id)).filter(Job.created_at >= yesterday).scalar() or 0
        matches_today = db.query(func.count(Match.id)).filter(Match.created_at >= yesterday).scalar() or 0
        accepted_today = db.query(func.count(Match.id)).filter(
            Match.created_at >= yesterday, Match.status == "accepted"
        ).scalar() or 0
        revenue_today = db.query(func.coalesce(func.sum(Payment.platform_fee), 0)).filter(
            Payment.created_at >= yesterday, Payment.status == "paid"
        ).scalar() or 0
        new_users = db.query(func.count(User.id)).filter(User.created_at >= yesterday).scalar() or 0
        completed_today = db.query(func.count(Job.id)).filter(
            Job.created_at >= yesterday, Job.status == "completed"
        ).scalar() or 0
        errors = db.query(func.count(Notification.id)).filter(
            Notification.created_at >= yesterday, Notification.type == "error"
        ).scalar() or 0
        contracts_today = db.query(func.count(Contract.id)).filter(Contract.created_at >= yesterday).scalar() or 0
        commissions_today = db.query(func.count(Commission.id)).filter(Commission.created_at >= yesterday).scalar() or 0

        metrics = {
            "jobs": jobs_today,
            "matches": matches_today,
            "accepted": accepted_today,
            "contracts": contracts_today,
            "completed": completed_today,
            "revenue": float(revenue_today),
            "new_users": new_users,
            "errors": errors,
            "commissions": commissions_today,
        }

        anomalies = _compute_anomalies(metrics, db)
        insights = generate_daily_insights(metrics, anomalies)

        # Store report for history
        existing = db.query(DailyReport).filter(DailyReport.report_date == today).first()
        if existing:
            existing.metrics = metrics
            existing.anomalies = anomalies
            existing.insights = insights
        else:
            db.add(DailyReport(
                report_date=today,
                metrics=metrics,
                anomalies=anomalies,
                insights=insights,
            ))
        db.commit()

        anomalies_html = "".join(f"<li style='color:#f87171'>{a}</li>" for a in anomalies) or "<li>none</li>"
        body = (
            f"Jobs posted: {jobs_today}<br/>"
            f"AI matches made: {matches_today}<br/>"
            f"Accepted: {accepted_today}<br/>"
            f"Contracts: {contracts_today}<br/>"
            f"Jobs completed: {completed_today}<br/>"
            f"Revenue (fees): {float(revenue_today):.2f} PLN<br/>"
            f"Referral commissions paid: {commissions_today}<br/>"
            f"New users: {new_users}<br/>"
            f"Errors: {errors}<br/><br/>"
            f"<b>Anomalies:</b><ul>{anomalies_html}</ul>"
            f"<b>AI recommendations:</b><br/>{insights}"
        )

        admins = db.query(User).filter(User.role == "admin").all()
        for admin in admins:
            notify_email(
                admin.email,
                "DROPIFY Daily AI Report",
                "Your daily automation report",
                body,
            )

        notify_n8n("daily-report", {
            **metrics,
            "anomalies": anomalies,
            "insights": insights[:500],
        })
        return {"metrics": metrics, "anomalies": anomalies, "insights": insights}
    except Exception as exc:
        logger.exception("Daily summary failed: %s", exc)
        db.rollback()
        return {"error": str(exc)}
    finally:
        db.close()


@shared_task(name="app.tasks.reports.process_referral_commissions")
def process_referral_commissions():
    """Referral 2.0 'Earn Forever': 2% L1 / 1% L2 of contract amount, 12-month window."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=1)
        contracts = (
            db.query(Contract)
            .filter(Contract.status == "completed", Contract.completed_at >= cutoff)
            .all()
        )
        created = 0
        for contract in contracts:
            client = db.get(User, contract.client_id)
            if not client or not client.referred_by:
                continue
            # 12-month earnings window since referred user registered
            if client.created_at:
                months_active = (datetime.utcnow() - client.created_at).days / 30.0
                if months_active > settings.REFERRAL_MONTHS:
                    continue

            # Level 1 (2%)
            l1 = db.get(User, client.referred_by)
            if l1:
                amount1 = round(contract.amount * settings.REFERRAL_RATE_L1, 2)
                existing1 = db.query(Commission).filter(
                    Commission.contract_id == contract.id, Commission.level == 1
                ).first()
                if amount1 > 0 and not existing1:
                    db.add(Commission(
                        referrer_id=l1.id,
                        referred_id=client.id,
                        contract_id=contract.id,
                        level=1,
                        rate=settings.REFERRAL_RATE_L1,
                        amount=amount1,
                        status="paid",
                    ))
                    create_notification(
                        db,
                        l1.id,
                        "Referral commission earned!",
                        f"You earned {amount1:.2f} PLN from a contract of {client.display_name}. (2% level-1 referral)",
                        "money",
                        l1.email,
                        "Referral commission earned!",
                    )
                    notify_n8n("referral-commission", {
                        "level": 1,
                        "amount": amount1,
                        "referrer_id": l1.id,
                        "referred_id": client.id,
                        "contract_id": contract.id,
                    })
                    created += 1

                # Level 2 (1%) — the referrer of the referrer
                if l1.referred_by:
                    l2 = db.get(User, l1.referred_by)
                    if l2:
                        amount2 = round(contract.amount * settings.REFERRAL_RATE_L2, 2)
                        existing2 = db.query(Commission).filter(
                            Commission.contract_id == contract.id, Commission.level == 2
                        ).first()
                        if amount2 > 0 and not existing2:
                            db.add(Commission(
                                referrer_id=l2.id,
                                referred_id=client.id,
                                contract_id=contract.id,
                                level=2,
                                rate=settings.REFERRAL_RATE_L2,
                                amount=amount2,
                                status="paid",
                            ))
                            create_notification(
                                db,
                                l2.id,
                                "Referral commission earned (level 2)!",
                                f"You earned {amount2:.2f} PLN from a second-level referral contract. (1% level-2)",
                                "money",
                                l2.email,
                                "Referral commission earned!",
                            )
                            notify_n8n("referral-commission", {
                                "level": 2,
                                "amount": amount2,
                                "referrer_id": l2.id,
                                "referred_id": client.id,
                                "contract_id": contract.id,
                            })
                            created += 1

        db.commit()
        return {"commissions_created": created}
    except Exception as exc:
        logger.exception("Referral commissions failed: %s", exc)
        db.rollback()
        return {"error": str(exc)}
    finally:
        db.close()


@shared_task(name="app.tasks.reports.auto_release_milestones")
def auto_release_milestones():
    """#5: auto-release milestones stuck in review for 48h (client silence = approval)."""
    db = SessionLocal()
    try:
        from app.routes.contracts import _release
        cutoff = datetime.utcnow() - timedelta(hours=48)
        stuck = (
            db.query(Milestone)
            .filter(Milestone.status == "in_review", Milestone.submitted_at < cutoff)
            .all()
        )
        released = 0
        for milestone in stuck:
            contract = db.get(Contract, milestone.contract_id)
            if not contract or contract.status != "in_progress":
                continue
            _release(db, contract, milestone, autopilot=True)
            freelancer = db.get(User, contract.freelancer_id)
            if freelancer:
                create_notification(
                    db,
                    freelancer.id,
                    "Milestone auto-released",
                    f"'{milestone.title}' ({milestone.amount:.2f} PLN) was released automatically after 48h — "
                    "the client did not object.",
                    "money",
                    freelancer.email,
                    "Milestone auto-released",
                )
            released += 1
        db.commit()
        return {"released": released}
    except Exception as exc:
        logger.exception("Auto-release failed: %s", exc)
        db.rollback()
        return {"error": str(exc)}
    finally:
        db.close()


@shared_task(name="app.tasks.reports.process_payouts")
def process_payouts():
    """#6: mark paid payments as paid_out (bank or stablecoin) and notify freelancers."""
    db = SessionLocal()
    try:
        paid = db.query(Payment).filter(Payment.status == "paid").all()
        processed = 0
        for payment in paid:
            freelancer = db.get(User, payment.contract.freelancer_id) if payment.contract else None
            method = payment.payout_method or (freelancer.payout_method if freelancer else "bank")
            address = payment.payout_address or (freelancer.payout_address if freelancer else None)
            payment.status = "paid_out"
            payment.payout_method = method
            payment.payout_address = address
            payment.payout_date = datetime.utcnow()
            if freelancer:
                create_notification(
                    db,
                    freelancer.id,
                    "Payout sent",
                    f"{payment.net_amount:.2f} PLN paid out via {method}"
                    + (f" ({address})" if method == "stablecoin" and address else "")
                    + ". Funds arrive in minutes (stablecoin) or 1-3 days (bank).",
                    "money",
                    freelancer.email,
                    "Payout sent",
                )
            notify_n8n("payout-processed", {
                "payment_id": payment.id,
                "contract_id": payment.contract_id,
                "amount": payment.net_amount,
                "method": method,
            })
            processed += 1
        db.commit()
        return {"payouts": processed}
    except Exception as exc:
        logger.exception("Payouts failed: %s", exc)
        db.rollback()
        return {"error": str(exc)}
    finally:
        db.close()


@shared_task(name="app.tasks.reports.auto_complete_overdue")
def auto_complete_overdue():
    """Close contracts that have been 'in_progress' for more than 60 days."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=60)
        overdue = (
            db.query(Contract)
            .filter(Contract.status == "in_progress", Contract.created_at < cutoff)
            .all()
        )
        for contract in overdue:
            contract.status = "completed"
            contract.completed_at = datetime.utcnow()
            job = db.get(Job, contract.job_id)
            if job:
                job.status = "completed"
        db.commit()
        return {"completed": len(overdue)}
    except Exception as exc:
        logger.exception("Auto-complete failed: %s", exc)
        db.rollback()
        return {"error": str(exc)}
    finally:
        db.close()
