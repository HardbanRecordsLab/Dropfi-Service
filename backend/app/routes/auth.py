from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import User, Referral
from app.schemas import UserCreate, UserLogin, UserOut, Token
from app.utils.emailer import notify_email
from app.utils.security import (
    hash_password, verify_password, create_access_token, make_referral_code,
    create_purpose_token, decode_purpose_token,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

PASSWORD_RESET_MINUTES = 30
EMAIL_VERIFY_MINUTES = 24 * 60


@router.post("/register", response_model=Token, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    referred_by = None
    if data.referral_code:
        referrer = db.query(User).filter(User.referral_code == data.referral_code).first()
        if referrer:
            referred_by = referrer.id

    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role=data.role,
        first_name=data.first_name,
        last_name=data.last_name,
        company=data.company,
        referral_code=make_referral_code(data.email),
        referred_by=referred_by,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if referred_by:
        db.add(Referral(referrer_id=referred_by, referred_id=user.id))
        db.commit()

    verify_token = create_purpose_token(user.id, "email_verify", EMAIL_VERIFY_MINUTES)
    notify_email(
        user.email, "Verify your DROPIFY email", "Welcome to DROPIFY!",
        "Click the button below to verify your email address.",
        cta_url=f"{settings.FRONTEND_URL}/verify-email?token={verify_token}", cta_label="Verify email",
    )

    token = create_access_token(user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    token = create_access_token(user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password")
def forgot_password(email: str = Body(..., embed=True), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.lower()).first()
    if user:
        token = create_purpose_token(user.id, "password_reset", PASSWORD_RESET_MINUTES)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        notify_email(
            user.email, "Reset your DROPIFY password", "Reset your password",
            f"Click the button below to set a new password. This link expires in {PASSWORD_RESET_MINUTES} minutes. "
            "If you didn't request this, you can ignore this email.",
            cta_url=reset_url, cta_label="Reset password",
        )
    # Always return the same message regardless of whether the email exists,
    # so this endpoint can't be used to enumerate registered accounts.
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(
    token: str = Body(..., embed=True),
    new_password: str = Body(..., min_length=8, embed=True),
    db: Session = Depends(get_db),
):
    user_id = decode_purpose_token(token, "password_reset")
    user = db.get(User, user_id) if user_id else None
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    user.password_hash = hash_password(new_password)
    db.commit()
    return {"message": "Password updated — you can now sign in."}


@router.post("/send-verification")
def send_verification(user: User = Depends(get_current_user)):
    if user.email_verified:
        return {"message": "Already verified"}
    token = create_purpose_token(user.id, "email_verify", EMAIL_VERIFY_MINUTES)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    notify_email(
        user.email, "Verify your DROPIFY email", "Confirm your email",
        "Click the button below to verify your email address.",
        cta_url=verify_url, cta_label="Verify email",
    )
    return {"message": "Verification email sent"}


@router.post("/verify-email")
def verify_email(token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    user_id = decode_purpose_token(token, "email_verify")
    user = db.get(User, user_id) if user_id else None
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")
    user.email_verified = True
    db.commit()
    return {"message": "Email verified"}
