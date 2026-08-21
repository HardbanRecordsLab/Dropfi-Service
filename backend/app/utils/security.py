import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: str, expires_days: int | None = None) -> str:
    payload = {
        "user_id": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc)
        + timedelta(days=expires_days or settings.ACCESS_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("purpose"):
            # A password-reset / email-verify token is signed with the same
            # SECRET_KEY but must never double as a full session token.
            return None
        return payload.get("user_id")
    except jwt.PyJWTError:
        return None


def create_purpose_token(user_id: str, purpose: str, expires_minutes: int = 30) -> str:
    """Short-lived, single-purpose JWT for password reset / email verification
    links — reuses SECRET_KEY (no separate DB-stored token table needed) but
    a `purpose` claim keeps it from being usable as a normal auth token."""
    payload = {
        "user_id": user_id,
        "purpose": purpose,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_purpose_token(token: str, expected_purpose: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("purpose") != expected_purpose:
            return None
        return payload.get("user_id")
    except jwt.PyJWTError:
        return None


def make_referral_code(email: str) -> str:
    seed = email.split("@")[0].lower()[:10].replace(".", "")
    code = f"{seed}-{secrets.token_hex(3)}"
    return code
