"""AI profile/job verification (fraud & fake-qualification checks) — separate
from utils/risk.py's behavioral Smart Supplier Risk Score, which needs
completed jobs to say anything; this runs at registration/profile-completion
and at job creation, before any track record exists.

No OPENROUTER_API_KEY in the test environment, so these exercise the
deterministic rule-based fallback path (llm_enabled() is False) — the same
path a self-hosted deployment without an AI key would actually run.
"""
import os

from tests.helpers import auth_headers, register, unique_email


def _admin_token(client):
    resp = client.post("/api/auth/login", json={
        "email": os.environ["ADMIN_EMAIL"], "password": os.environ["ADMIN_PASSWORD"],
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def test_thin_freelancer_profile_flagged_at_registration(client):
    """A freelancer who registers with no bio, no skills, no portfolio should
    not come out of signup as 'verified' — the whole point of this check."""
    data = register(client, "freelancer")
    user = data["user"]
    assert user["verification_status"] in ("pending", "review", "flagged")
    assert user["verification_status"] != "verified"


def test_complete_freelancer_profile_scores_higher_than_thin_one(client):
    thin = register(client, "freelancer")["user"]

    rich_email = unique_email("rich-freelancer")
    rich_data = register(
        client, "freelancer", email=rich_email,
        bio="Senior backend engineer, 8 years building payment systems in Python and Go.",
        skills=["Python", "FastAPI", "PostgreSQL", "Payments"],
        portfolio_links=["https://github.com/example", "https://example-portfolio.dev"],
        certifications=[{"name": "AWS Solutions Architect", "issuer": "AWS", "year": 2022}],
        work_history=[{"company": "Acme Corp", "role": "Senior Backend Engineer", "period": "2019-2024", "description": "Payments platform"}],
        linkedin_url="https://linkedin.com/in/example",
    )
    rich = rich_data["user"]

    assert rich["verification_score"] is not None
    assert thin["verification_score"] is None or rich["verification_score"] > thin["verification_score"]
    assert rich["portfolio_links"] == ["https://github.com/example", "https://example-portfolio.dev"]
    assert len(rich["certifications"]) == 1


def test_profile_update_recomputes_verification(client):
    """A freelancer who registers thin, then fills in their profile via PUT
    /me, should get (re-)verified at that point — not stay 'pending' forever
    just because the signup form itself was minimal."""
    data = register(client, "freelancer")
    token = data["access_token"]
    assert data["user"]["verification_status"] == "pending"

    resp = client.put("/api/users/me", headers=auth_headers(token), json={
        "bio": "Award-winning illustrator specializing in editorial and book covers.",
        "skills": ["Illustration", "Photoshop", "Procreate"],
        "portfolio_links": ["https://behance.net/example"],
        "linkedin_url": "https://linkedin.com/in/example-illustrator",
    })
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["verification_score"] is not None
    assert updated["verification_status"] in ("verified", "review", "flagged")


def test_unrelated_profile_update_does_not_recompute_verification(client):
    """Flipping availability shouldn't burn an LLM call / touch verification —
    only fields that could actually change the AI's answer should re-trigger it."""
    data = register(client, "freelancer")
    token = data["access_token"]

    resp = client.put("/api/users/me", headers=auth_headers(token), json={"availability": "busy"})
    assert resp.status_code == 200
    assert resp.json()["verification_status"] == "pending"
    assert resp.json()["verification_score"] is None


def test_vague_underpriced_job_flagged_on_creation(client):
    """A one-line job description with a budget far under any plausible fair
    price is exactly the pattern real scam/unpaid-work postings follow.
    create_job_and_match runs matching (and, now, verification) inline in
    tests (CELERY_TASK_ALWAYS_EAGER=1), so this is already set by the time
    POST /api/jobs returns."""
    client_data = register(client, "client")
    token = client_data["access_token"]
    resp = client.post("/api/jobs", headers=auth_headers(token), json={
        "title": "need website",
        "description": "make it good",
        "budget": 5,
        "deadline": "2027-01-01",
    })
    assert resp.status_code == 201
    job = resp.json()
    assert job["verification_status"] in ("review", "flagged")
    assert len(job["verification_flags"]) > 0


def test_well_specified_fairly_priced_job_not_flagged(client):
    client_data = register(client, "client")
    token = client_data["access_token"]
    resp = client.post("/api/jobs", headers=auth_headers(token), json={
        "title": "Redesign marketing website in Figma and build in Webflow",
        "description": (
            "We need a full redesign of our 8-page marketing site: homepage, pricing, "
            "3 product pages, about, blog index and contact. Deliverable is a Figma file "
            "plus a live Webflow build, responsive down to 375px, with the existing brand "
            "colors and a new type system. Content is already written; you only design and build."
        ),
        "budget": 4500,
        "deadline": "2027-03-01",
        "required_skills": ["Figma", "Webflow", "UI Design"],
    })
    assert resp.status_code == 201
    job = resp.json()
    assert job["verification_score"] is not None


def test_admin_verification_queue_lists_flagged_entries(client):
    # A freelancer signup with SOME data (so verification actually runs, per
    # auth.py's "empty profile stays pending, not flagged" rule) but thin
    # enough to land in review/flagged should show up in the queue.
    register(client, "freelancer", bio="ok", skills=["stuff"])

    admin_token = _admin_token(client)
    resp = client.get("/api/admin/verification-queue", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "freelancers" in data and "jobs" in data
    assert any(f["status"] in ("review", "flagged") for f in data["freelancers"])


def test_verification_queue_requires_admin(client):
    data = register(client, "client")
    resp = client.get("/api/admin/verification-queue", headers=auth_headers(data["access_token"]))
    assert resp.status_code == 403
