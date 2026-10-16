from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, Job, Match, Contract, Message
from app.utils.messaging import scan_message, summarize_thread, suggest_replies, translate_text
from app.utils.n8n import notify_n8n
from app.utils.notifications import create_notification
from app.utils.ratelimit import hit

router = APIRouter(prefix="/messages", tags=["Messages"])

MAX_BODY = 4000


def load_thread(db: Session, match_id: str, user: User) -> tuple[Match, Job, Contract | None]:
    """Fetch a match thread and enforce that `user` is the client, the matched freelancer or admin."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Thread not found")
    job = db.get(Job, match.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Thread not found")
    if user.id not in (job.client_id, match.freelancer_id) and user.role != "admin":
        raise HTTPException(status_code=404, detail="Thread not found")
    contract = db.query(Contract).filter(Contract.match_id == match.id).first()
    return match, job, contract


def _role_of(user_id: str, job: Job) -> str:
    return "client" if user_id == job.client_id else "freelancer"


def _msg_out(m: Message, viewer_id: str, lang: str | None) -> dict:
    translated = (m.translations or {}).get(lang) if lang else None
    return {
        "id": m.id,
        "sender_id": m.sender_id,
        "mine": m.sender_id == viewer_id,
        "body": m.body,
        "translated": translated,
        "flagged": bool(m.flagged),
        "flag_reasons": m.flag_reasons or [],
        "read_at": m.read_at,
        "created_at": m.created_at,
    }


def send_message(db: Session, user: User, match_id: str, body: str) -> dict:
    """Shared by the REST route and the MCP `send_message` tool."""
    hit(f"msg:{user.id}", 30, 60)
    body = (body or "").strip()
    if not body:
        raise HTTPException(status_code=422, detail="Message is empty")
    if len(body) > MAX_BODY:
        raise HTTPException(status_code=422, detail=f"Message longer than {MAX_BODY} characters")
    match, job, contract = load_thread(db, match_id, user)
    if user.role == "admin" and user.id not in (job.client_id, match.freelancer_id):
        raise HTTPException(status_code=403, detail="Admins can read threads but not post in them")
    if match.status == "rejected":
        raise HTTPException(status_code=409, detail="This match was rejected — the thread is read-only")

    # Mask contact details until there is a contract (fee-leak + scam protection).
    safe_body, reasons = scan_message(body, mask=contract is None)
    msg = Message(match_id=match.id, sender_id=user.id, body=safe_body,
                  flagged=bool(reasons), flag_reasons=reasons or None)
    db.add(msg)
    db.commit()
    db.refresh(msg)

    recipient_id = match.freelancer_id if user.id == job.client_id else job.client_id
    recipient = db.get(User, recipient_id)
    create_notification(
        db, recipient_id,
        title=f"New message: {job.title[:80]}",
        body=f"{user.display_name}: {safe_body[:140]}",
        ntype="message",
    )
    if reasons:
        notify_n8n("message-flagged", {
            "match_id": match.id, "job_id": job.id, "sender_id": user.id, "reasons": reasons,
        })
    return {
        **_msg_out(msg, user.id, None),
        "warning": (
            "Contact details are hidden until a contract is signed — payments outside DROPIFY "
            "are not protected by escrow." if reasons and contract is None else
            "Keep payments on DROPIFY so escrow and the refund guarantee protect you." if reasons else None
        ),
        "recipient": recipient.display_name if recipient else None,
    }


@router.get("/threads")
def list_threads(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """All conversations the user is part of, newest activity first, with unread counts."""
    q = db.query(Match, Job).join(Job, Job.id == Match.job_id)
    if user.role == "freelancer":
        q = q.filter(Match.freelancer_id == user.id)
    else:
        q = q.filter(Job.client_id == user.id)
    pairs = q.all()
    if not pairs:
        return []
    match_ids = [m.id for m, _ in pairs]

    last_at = dict(
        db.query(Message.match_id, func.max(Message.created_at))
        .filter(Message.match_id.in_(match_ids)).group_by(Message.match_id).all()
    )
    unread = dict(
        db.query(Message.match_id, func.count(Message.id))
        .filter(Message.match_id.in_(match_ids), Message.sender_id != user.id, Message.read_at.is_(None))
        .group_by(Message.match_id).all()
    )
    other_ids = {m.freelancer_id if user.role != "freelancer" else j.client_id for m, j in pairs}
    others = {u.id: u for u in db.query(User).filter(User.id.in_(other_ids)).all()}

    threads = []
    for match, job in pairs:
        # Only surface threads that have messages, or live matches where a conversation can start.
        if match.id not in last_at and match.status == "rejected":
            continue
        other = others.get(match.freelancer_id if user.role != "freelancer" else job.client_id)
        last = None
        if match.id in last_at:
            lm = (db.query(Message).filter(Message.match_id == match.id)
                  .order_by(Message.created_at.desc()).first())
            last = {"body": lm.body[:160], "mine": lm.sender_id == user.id, "created_at": lm.created_at}
        threads.append({
            "match_id": match.id,
            "job_id": job.id,
            "job_title": job.title,
            "match_status": match.status,
            "score": match.score,
            "other_name": other.display_name if other else "",
            "other_id": other.id if other else None,
            "last_message": last,
            "last_at": last_at.get(match.id),
            "unread": unread.get(match.id, 0),
        })
    epoch = datetime.min.replace(tzinfo=timezone.utc)

    def _key(t):
        ts = t["last_at"]
        if ts is None:
            return epoch
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)

    threads.sort(key=_key, reverse=True)
    return threads


@router.get("/unread-count")
def unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = (db.query(func.count(Message.id))
         .join(Match, Match.id == Message.match_id).join(Job, Job.id == Match.job_id)
         .filter(Message.sender_id != user.id, Message.read_at.is_(None)))
    if user.role == "freelancer":
        q = q.filter(Match.freelancer_id == user.id)
    else:
        q = q.filter(Job.client_id == user.id)
    return {"unread": q.scalar() or 0}


@router.get("/{match_id}")
def get_thread(
    match_id: str,
    lang: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    match, job, contract = load_thread(db, match_id, user)
    msgs = (db.query(Message).filter(Message.match_id == match.id)
            .order_by(Message.created_at.asc()).limit(500).all())
    now = datetime.now(timezone.utc)
    changed = False
    for m in msgs:
        if m.sender_id != user.id and m.read_at is None and user.id in (job.client_id, match.freelancer_id):
            m.read_at = now
            changed = True
    if changed:
        db.commit()
    return {
        "match_id": match.id,
        "job_id": job.id,
        "job_title": job.title,
        "match_status": match.status,
        "has_contract": contract is not None,
        "contract_id": contract.id if contract else None,
        "messages": [_msg_out(m, user.id, lang) for m in msgs],
    }


@router.post("/{match_id}")
def post_message(
    match_id: str,
    body: str = Body(..., embed=True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return send_message(db, user, match_id, body)


@router.post("/{match_id}/translate")
def translate_thread(
    match_id: str,
    lang: str = Body("pl", embed=True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Translate the other party's messages into `lang` (cached per message)."""
    lang = "pl" if lang == "pl" else "en"
    match, _job, _ = load_thread(db, match_id, user)
    msgs = (db.query(Message).filter(Message.match_id == match.id, Message.sender_id != user.id)
            .order_by(Message.created_at.desc()).limit(50).all())
    translated, unavailable = 0, False
    for m in msgs:
        cache = dict(m.translations or {})
        if lang in cache:
            continue
        out = translate_text(m.body, lang)
        if out is None:
            unavailable = True
            break
        cache[lang] = out
        m.translations = cache
        translated += 1
    db.commit()
    return {"translated": translated, "ai_available": not unavailable, "lang": lang}


@router.get("/{match_id}/summary")
def thread_summary(
    match_id: str,
    language: str = "pl",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    match, job, _ = load_thread(db, match_id, user)
    msgs = (db.query(Message).filter(Message.match_id == match.id)
            .order_by(Message.created_at.asc()).limit(200).all())
    if not msgs:
        raise HTTPException(status_code=404, detail="No messages yet")
    lines = [(_role_of(m.sender_id, job), m.body) for m in msgs]
    return summarize_thread(job.title, lines, "pl" if language == "pl" else "en")


@router.get("/{match_id}/suggest-replies")
def thread_suggestions(
    match_id: str,
    language: str = "pl",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    match, job, _ = load_thread(db, match_id, user)
    msgs = (db.query(Message).filter(Message.match_id == match.id)
            .order_by(Message.created_at.desc()).limit(15).all())
    lines = [(_role_of(m.sender_id, job), m.body) for m in reversed(msgs)]
    role = _role_of(user.id, job)
    return {"replies": suggest_replies(job.title, role, lines, "pl" if language == "pl" else "en")}
