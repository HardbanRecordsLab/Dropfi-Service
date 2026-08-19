from sqlalchemy.orm import Session

from app.models import Notification
from app.utils.emailer import notify_email


def create_notification(db: Session, user_id: str, title: str, body: str = "", ntype: str = "info", user_email: str | None = None, email_subject: str | None = None) -> Notification:
    n = Notification(user_id=user_id, type=ntype, title=title, body=body)
    db.add(n)
    try:
        db.commit()
    except Exception:
        db.rollback()
        db.add(n)
        db.commit()
    if user_email:
        notify_email(user_email, email_subject or title, title, body)
    return n
