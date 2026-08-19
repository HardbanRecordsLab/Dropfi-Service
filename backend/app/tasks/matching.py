"""Core AI matching pipeline (Celery task).

Flow:
1. Analyze job with Claude (fallback: rules) → category, skills, fair price
2. Generate job embedding
3. Semantic search (pgvector / Python) for candidate freelancers
4. Score each candidate (semantic, rating, price fit, availability)
5. Save top 3-5 matches + notify freelancers
"""
import json
import logging

from celery import shared_task
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User, Job, Match
from app.utils.ai import analyze_job, embed_text, job_search_text, semantic_search_freelancers
from app.utils.scoring import calculate_match_score
from app.utils.notifications import create_notification
from app.utils.n8n import notify_n8n

logger = logging.getLogger(__name__)

TOP_N = 3


def run_matching(db: Session, job_id: str) -> int:
    job = db.get(Job, job_id)
    if not job:
        logger.error("Job %s not found", job_id)
        return 0

    if job.status not in ("open", "matched"):
        return 0

    # 1. Analyze job
    analysis = analyze_job(job.title, job.description, job.budget, str(job.deadline), job.location)
    job.category = analysis.get("category") or job.category
    job.subcategory = analysis.get("subcategory") or ""
    job.required_skills = analysis.get("skills") or job.required_skills
    job.ai_analysis = analysis
    db.commit()

    # 2. Embedding
    query_vec = embed_text(job_search_text(job.title, job.description, analysis))
    job.embedding_json = json.dumps(query_vec)
    db.commit()

    # 3. Semantic search candidates (exclude freelancers already matched on this job)
    interacted = {
        m.freelancer_id
        for m in db.query(Match).filter(Match.job_id == job.id).all()
    }
    fallback_run = bool(interacted)
    candidates = semantic_search_freelancers(db, query_vec, limit=20, exclude_ids=interacted)
    if not candidates:
        logger.info("No freelancer candidates for job %s", job_id)
        return 0

    # 4. Score
    scored = []
    for user_id, semantic in candidates:
        freelancer = db.get(User, user_id)
        if not freelancer or freelancer.availability != "available":
            continue
        if freelancer.hourly_rate and freelancer.hourly_rate * 8 > job.budget:
            continue
        score = calculate_match_score(
            semantic=semantic,
            rating=freelancer.rating,
            budget=job.budget,
            fair_price=float(analysis.get("fair_price") or job.budget),
            deadline=job.deadline,
        )
        if score >= 0.45:
            scored.append((freelancer, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    # 5. Save top matches (dedupe existing)
    existing = {
        m.freelancer_id
        for m in db.query(Match).filter(Match.job_id == job.id, Match.status == "pending").all()
    }
    created = 0
    for freelancer, score in scored[:TOP_N]:
        if freelancer.id in existing:
            continue
        db.add(Match(
            job_id=job.id,
            freelancer_id=freelancer.id,
            score=score,
            matched_by="ai",
            status="pending",
        ))
        create_notification(
            db,
            freelancer.id,
            "New job match!" if not fallback_run else "PRIORITY: fallback match!",
            f"AI matched you to: {job.title} (score {score:.0%}). Budget: {job.budget:.2f} PLN. Deadline: {job.deadline}."
            + (" Previous candidate declined — you are next in line." if fallback_run else ""),
            "priority" if fallback_run else "match",
            freelancer.email,
            f"New match: {job.title}",
        )
        notify_n8n("match-created", {
            "job_id": job.id,
            "job_title": job.title,
            "freelancer_id": freelancer.id,
            "freelancer_name": freelancer.display_name,
            "score": score,
            "fallback": fallback_run,
        })
        created += 1

    db.commit()

    # Feature #13: AI Proposal Autopilot — auto-accept matches for configured freelancers
    if created:
        auto_accepted = 0
        fresh = (
            db.query(Match)
            .filter(Match.job_id == job.id, Match.status == "pending")
            .all()
        )
        for m in fresh:
            db.refresh(m)
            if m.status != "pending":
                continue
            freelancer = db.get(User, m.freelancer_id)
            if not freelancer or not freelancer.auto_accept_enabled:
                continue
            min_score = freelancer.auto_accept_min_score or 0.6
            if m.score < min_score:
                continue
            if freelancer.auto_accept_min_budget and job.budget < freelancer.auto_accept_min_budget:
                continue
            from app.routes.matches import create_contract
            create_contract(db, m, freelancer, autopilot=True)
            create_notification(
                db,
                freelancer.id,
                "Autopilot accepted the match for you",
                f"AI Autopilot accepted '{job.title}' automatically (score {m.score:.0%}). "
                "Disable it in your profile if you want manual control.",
                "autopilot",
                freelancer.email,
                "Autopilot accepted a match",
            )
            auto_accepted += 1
            break  # one contract per job — create_contract rejects other pending matches
        if auto_accepted:
            logger.info("Autopilot accepted %d matches on job %s", auto_accepted, job_id)
            notify_n8n("autopilot-accepted", {
                "job_id": job.id,
                "count": auto_accepted,
            })

    logger.info("Created %d matches for job %s", created, job_id)
    return created


@shared_task(name="app.tasks.matching.trigger_ai_matching")
def trigger_ai_matching(job_id: str) -> dict:
    db = SessionLocal()
    try:
        count = run_matching(db, job_id)
        return {"job_id": job_id, "matches_created": count}
    except Exception as exc:
        logger.exception("Matching failed for job %s: %s", job_id, exc)
        db.rollback()
        return {"job_id": job_id, "error": str(exc)}
    finally:
        db.close()


@shared_task(name="app.tasks.matching.recommend_jobs_to_freelancers")
def recommend_jobs_to_freelancers():
    """Nightly: re-match open jobs against freelancers who joined recently."""
    db = SessionLocal()
    try:
        open_jobs = db.query(Job).filter(Job.status == "open").limit(50).all()
        total = 0
        for job in open_jobs:
            total += run_matching(db, job.id)
        return {"jobs_processed": len(open_jobs), "matches_created": total}
    except Exception as exc:
        logger.exception("Nightly matching failed: %s", exc)
        db.rollback()
        return {"error": str(exc)}
    finally:
        db.close()
