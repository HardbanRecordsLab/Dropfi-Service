"""Seed demo data: sample freelancers, a demo client, and a sample job with AI matching."""
from app.database import SessionLocal, init_db
from app.models import User, Job
from app.utils.security import hash_password, make_referral_code
from datetime import date, timedelta


def main():
    init_db()
    db = SessionLocal()
    try:
        client = db.query(User).filter(User.email == "demo@dropify.app").first()
        if not client:
            client = User(
                email="demo@dropify.app",
                password_hash=hash_password("demo1234"),
                role="client",
                first_name="Demo",
                last_name="Shop",
                company="Demo E-commerce",
                referral_code=make_referral_code("demo@dropify.app"),
            )
            db.add(client)

        freelancers = [
            ("foto@dropify.app", "Krzysztof", "Nowak", "Professional product & fashion photographer, 8 years experience", "Warsaw",
             ["photography", "retouching", "video", "graphic design"], 120, 4.8),
            ("studio@dropify.app", "Magdalena", "Kowalska", "E-commerce photo studio, white background specialists", "Warsaw",
             ["photography", "retouching", "e-commerce"], 100, 4.2),
            ("dev@dropify.app", "Jan", "Lewandowski", "Full-stack developer, Shopify & WooCommerce expert", "Cracow",
             ["web development", "e-commerce", "ui/ux"], 150, 4.5),
            ("design@dropify.app", "Anna", "Wiśniewska", "Brand identity designer, logos, packaging, social media", "Gdansk",
             ["graphic design", "ui/ux", "marketing"], 90, 4.6),
            ("copy@dropify.app", "Marek", "Zieliński", "SEO copywriter, PL/EN blog and product descriptions", "Remote",
             ["copywriting", "seo", "marketing", "translation"], 80, 4.4),
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
                description="We need a professional photographer for 100 product photos with white background, retouching included. Products are clothing and accessories. Deadline 5 days, Warsaw preferred.",
                budget=3500,
                deadline=date.today() + timedelta(days=5),
                location="Warsaw",
                required_skills=["photography", "retouching"],
                client_id=client.id,
            )
            db.add(job)
            db.commit()
            print(f"Job created: {job.id}")
            from app.tasks.matching import trigger_ai_matching
            trigger_ai_matching(job.id)
            print("AI matching triggered.")

        print("Seed complete. Demo accounts: demo@dropify.app / demo1234")
        print("Freelancer accounts: foto@dropify.app, studio@dropify.app, dev@dropify.app, design@dropify.app, copy@dropify.app / demo1234")
    finally:
        db.close()


if __name__ == "__main__":
    main()
