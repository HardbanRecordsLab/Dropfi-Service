import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.database import init_db, SessionLocal
from app.routes import (
    auth, users, jobs, matches, ratings, analytics, contracts,
    admin, plans, notifications, webhooks, referrals, n8n,
    factory, payments, copilot, developer, fx, integrations,
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
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/api/health")
def health():
    return {"status": "ok", "message": "DROPIFY is running", "version": settings.APP_VERSION}


@app.get("/")
def root():
    return {"message": "Welcome to DROPIFY API", "docs": "/docs"}
