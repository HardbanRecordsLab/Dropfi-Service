import logging
import uuid
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.database import init_db, SessionLocal
from app.routes import (
    auth, users, jobs, matches, ratings, analytics, contracts,
    admin, plans, notifications, webhooks, referrals, n8n,
    factory, payments, copilot, developer, fx, integrations, invoices, badges, radar,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def seed_admin_and_demo() -> None:
    from app.models import User, Job
    from app.utils.security import hash_password, make_referral_code
    from datetime import date, timedelta

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if not admin:
            db.add(User(
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                role="admin",
                first_name="DROPIFY",
                last_name="Admin",
                referral_code=make_referral_code(settings.ADMIN_EMAIL),
            ))
            db.commit()
            logger.info("Admin user created: %s", settings.ADMIN_EMAIL)

        if settings.SEED_DEMO_DATA:
            demo_client = db.query(User).filter(User.email == "demo@dropify.app").first()
            if not demo_client:
                demo_client = User(
                    email="demo@dropify.app",
                    password_hash=hash_password("demo1234"),
                    role="client",
                    first_name="Demo",
                    last_name="Shop",
                    company="Demo E-commerce",
                    referral_code=make_referral_code("demo@dropify.app"),
                )
                db.add(demo_client)
                db.commit()

            freelancers = [
                ("foto@dropify.app", "Krzysztof", "Nowak", "Professional product & fashion photographer", "Warsaw",
                 ["photography", "retouching", "video", "graphic design"], 120, 4.8),
                ("studio@dropify.app", "Magdalena", "Kowalska", "E-commerce photo studio, white background specialists", "Warsaw",
                 ["photography", "retouching", "e-commerce"], 100, 4.2),
                ("dev@dropify.app", "Jan", "Lewandowski", "Full-stack developer, Shopify & WooCommerce expert", "Cracow",
                 ["web development", "e-commerce", "ui/ux", "coding"], 150, 4.5),
                ("design@dropify.app", "Anna", "Wiśniewska", "Brand identity designer, logos, packaging", "Gdansk",
                 ["graphic design", "ui/ux", "marketing"], 90, 4.6),
            ]
            for email, fn, ln, bio, loc, skills, rate, rating in freelancers:
                if not db.query(User).filter(User.email == email).first():
                    db.add(User(
                        email=email,
                        password_hash=hash_password("demo1234"),
                        role="freelancer",
                        first_name=fn,
                        last_name=ln,
                        bio=bio,
                        location=loc,
                        skills=skills,
                        languages=["Polish", "English"],
                        hourly_rate=rate,
                        rating=rating,
                        rating_count=5,
                        referral_code=make_referral_code(email),
                    ))
            db.commit()

            if db.query(Job).count() == 0:
                job = Job(
                    title="100 product photos for e-commerce",
                    description="We need a professional photographer for 100 product photos with white background, retouching included. Products are clothing and accessories. Deadline 5 days, Warsaw.",
                    budget=3500,
                    deadline=date.today() + timedelta(days=5),
                    location="Warsaw",
                    required_skills=["photography", "retouching"],
                    client_id=demo_client.id,
                )
                db.add(job)
                db.commit()
                logger.info("Demo job created")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("DROPIFY starting up...")
    init_db()
    seed_admin_and_demo()
    yield
    logger.info("DROPIFY shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered B2B marketplace: automatic matching of jobs to freelancers & suppliers.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 1)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms}ms"
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms) [{request_id}]")
    return response

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(matches.router, prefix="/api")
app.include_router(ratings.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(contracts.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(plans.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(referrals.router, prefix="/api")
app.include_router(n8n.router, prefix="/api")
app.include_router(factory.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(copilot.router, prefix="/api")
app.include_router(developer.router, prefix="/api")
app.include_router(fx.router, prefix="/api")
app.include_router(integrations.router, prefix="/api")
app.include_router(invoices.router, prefix="/api")
app.include_router(badges.router, prefix="/api")
app.include_router(radar.router, prefix="/api")


@app.get("/api/health")
def health(request: Request):
    import redis as redis_lib
    from sqlalchemy import text

    checks = {"status": "ok", "version": settings.APP_VERSION, "checks": {}}

    # Database check
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["checks"]["database"] = "ok"
    except Exception as e:
        checks["checks"]["database"] = f"error: {type(e).__name__}"
        checks["status"] = "degraded"

    # Redis check
    try:
        r = redis_lib.from_url(settings.REDIS_URL, socket_timeout=2)
        r.ping()
        r.close()
        checks["checks"]["redis"] = "ok"
    except Exception as e:
        checks["checks"]["redis"] = f"error: {type(e).__name__}"
        checks["status"] = "degraded"

    # API keys check — only visible to authenticated admins
    auth_header = request.headers.get("Authorization", "")
    is_admin = False
    if auth_header.startswith("Bearer "):
        try:
            from app.utils.security import decode_access_token
            token = auth_header.split(" ", 1)[1]
            payload = decode_access_token(token)
            from app.database import SessionLocal as _SL
            _db = _SL()
            from app.models import User
            _user = _db.query(User).filter(User.id == payload.get("sub")).first()
            is_admin = _user is not None and _user.role == "admin"
            _db.close()
        except Exception:
            pass

    if is_admin:
        checks["checks"]["llm_api"] = (
            f"configured ({settings.LLM_MODEL})" if settings.OPENROUTER_API_KEY else "missing (rule-based fallback active)"
        )
        checks["checks"]["openai_embeddings"] = "configured" if settings.OPENAI_API_KEY else "missing (local embedding fallback)"
        checks["checks"]["stripe"] = "configured" if settings.STRIPE_SECRET_KEY else "missing (demo mode)"

    return checks


@app.get("/")
def root():
    return {"message": "Welcome to DROPIFY API", "docs": "/docs"}
