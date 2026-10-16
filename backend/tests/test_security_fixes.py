"""Regression tests for the audit fixes (escrow, access control, PII, ratings)."""
from datetime import date, timedelta

from app.config import settings
from tests.helpers import auth_headers, make_freelancer, register


def _future(days: int) -> str:
    return str(date.today() + timedelta(days=days))


DOMAINS = {
    "matches": ("Ceramic tableware product photographer, glaze close-ups", ["ceramics photography"], "Ceramic tableware photo shoot", "Photograph our ceramic tableware collection with glaze close-ups."),
    "pii": ("Bicycle parts technical illustrator, exploded diagrams", ["technical illustration"], "Bicycle parts exploded diagrams", "Technical illustration of bicycle parts as exploded diagrams."),
    "stripe": ("Perfume bottle 3D renderer, glass and liquid shaders", ["3d rendering"], "Perfume bottle 3D renders", "Photoreal 3D renders of perfume bottles, glass and liquid shaders."),
    "dispute": ("Beekeeping supplies Allegro copywriter, honey products", ["allegro copywriting"], "Honey and beekeeping listings copy", "Allegro listing copy for honey and beekeeping supplies."),
    "close": ("Pet food packaging translator German Polish", ["german translation"], "Translate pet food packaging to German", "Translate pet food packaging texts from Polish to German."),
    "rating": ("Vintage furniture restoration video editor, reels", ["video editing"], "Furniture restoration reels", "Edit short reels about vintage furniture restoration."),
}


def _contract(client, domain):
    bio, skills, title, desc = DOMAINS[domain]
    fr = make_freelancer(client, bio=bio, skills=skills)
    cl = register(client, "client")
    c_h, f_h = auth_headers(cl["access_token"]), auth_headers(fr["access_token"])
    job = client.post("/api/jobs", headers=c_h, json={
        "title": title,
        "description": desc,
        "budget": 2400, "deadline": _future(10),
    }).json()
    match = next(m for m in client.get(f"/api/matches/job/{job['id']}", headers=c_h).json()
                 if m["freelancer_id"] == fr["user"]["id"])
    contract = client.post(f"/api/matches/{match['id']}/accept", headers=f_h).json()
    return cl, fr, job, contract, c_h, f_h


def test_other_client_cannot_read_job_matches(client):
    cl, fr, job, contract, c_h, f_h = _contract(client, "matches")
    intruder = register(client, "client")
    resp = client.get(f"/api/matches/job/{job['id']}", headers=auth_headers(intruder["access_token"]))
    assert resp.status_code == 403


def test_public_job_payload_has_no_client_pii(client):
    cl, fr, job, contract, c_h, f_h = _contract(client, "pii")
    public = client.get(f"/api/jobs/{job['id']}").json()
    assert public["client"] is None or "email" not in public["client"]
    assert public["deliverables"] is None
    listing = client.get("/api/jobs?status=").json()
    for item in listing:
        if item.get("client"):
            assert "email" not in item["client"] and "payout_address" not in item["client"]


def test_release_requires_payment_when_stripe_enabled(client, monkeypatch):
    cl, fr, job, contract, c_h, f_h = _contract(client, "stripe")
    m = contract["milestones"][0]
    assert client.post(f"/api/contracts/{contract['id']}/milestones/{m['id']}/submit", headers=f_h).status_code == 200
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_fake")
    resp = client.post(f"/api/contracts/{contract['id']}/milestones/{m['id']}/release", headers=c_h)
    assert resp.status_code == 402
    detail = client.get(f"/api/contracts/{contract['id']}", headers=c_h).json()
    assert detail["milestones"][0]["status"] == "in_review"


def test_no_release_on_disputed_contract_and_no_double_release(client):
    cl, fr, job, contract, c_h, f_h = _contract(client, "dispute")
    m = contract["milestones"][0]
    client.post(f"/api/contracts/{contract['id']}/milestones/{m['id']}/submit", headers=f_h)
    assert client.post(f"/api/contracts/{contract['id']}/milestones/{m['id']}/release", headers=c_h).status_code == 200
    again = client.post(f"/api/contracts/{contract['id']}/milestones/{m['id']}/release", headers=c_h)
    assert again.status_code == 400

    m2 = contract["milestones"][1]
    client.post(f"/api/contracts/{contract['id']}/milestones/{m2['id']}/submit", headers=f_h)
    assert client.post(f"/api/contracts/{contract['id']}/dispute", headers=f_h,
                       json={"reason": "Client is unresponsive about the review"}).status_code == 200
    blocked = client.post(f"/api/contracts/{contract['id']}/milestones/{m2['id']}/release", headers=c_h)
    assert blocked.status_code == 409


def test_freelancer_cannot_close_contract_to_dodge_refund(client):
    cl, fr, job, contract, c_h, f_h = _contract(client, "close")
    assert client.post(f"/api/jobs/{job['id']}/complete", headers=f_h).status_code == 200
    detail = client.get(f"/api/contracts/{contract['id']}", headers=c_h).json()
    assert detail["status"] == "in_progress"
    # client can't close either while escrow is unreleased
    assert client.post(f"/api/jobs/{job['id']}/complete", headers=c_h).status_code == 400


def test_ratings_need_completed_contract_with_that_user(client):
    cl, fr, job, contract, c_h, f_h = _contract(client, "rating")
    sock = register(client, "client")
    resp = client.post("/api/ratings", headers=auth_headers(sock["access_token"]),
                       json={"to_user_id": fr["user"]["id"], "job_id": job["id"], "score": 5})
    assert resp.status_code == 403
    resp = client.post("/api/ratings", headers=auth_headers(sock["access_token"]),
                       json={"to_user_id": fr["user"]["id"], "score": 5})
    assert resp.status_code == 422
    # in-progress contract is not enough
    resp = client.post("/api/ratings", headers=c_h, json={"to_user_id": fr["user"]["id"], "job_id": job["id"], "score": 5})
    assert resp.status_code == 403


def test_job_update_cannot_force_status_or_negative_budget(client):
    cl = register(client, "client")
    c_h = auth_headers(cl["access_token"])
    job = client.post("/api/jobs", headers=c_h, json={
        "title": "Logo for a bakery", "description": "Simple, warm logo for a family bakery in Lodz.",
        "budget": 500, "deadline": _future(5),
    }).json()
    assert client.put(f"/api/jobs/{job['id']}", headers=c_h, json={"status": "completed"}).status_code == 422
    assert client.put(f"/api/jobs/{job['id']}", headers=c_h, json={"budget": -10}).status_code == 422


def test_paid_plan_needs_checkout_when_stripe_enabled(client, monkeypatch):
    import sys
    import types

    class _Session:
        url = "https://checkout.stripe.test/s/1"

    fake = types.SimpleNamespace(api_key=None, checkout=types.SimpleNamespace(
        Session=types.SimpleNamespace(create=lambda **kw: _Session())))
    monkeypatch.setitem(sys.modules, "stripe", fake)
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_fake")
    u = register(client, "client")
    h = auth_headers(u["access_token"])
    resp = client.post("/api/plans/subscribe?plan=pro", headers=h).json()
    assert resp["mode"] == "stripe" and resp["checkout_url"]
    assert client.get("/api/auth/me", headers=h).json()["plan"] == "free"
