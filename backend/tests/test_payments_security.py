"""Regression tests for the two payment-security fixes:
1. The Stripe webhook must reject all traffic when STRIPE_WEBHOOK_SECRET is
   unset, rather than trusting an unsigned/unverified body (previously any
   caller could forge a 'checkout.session.completed' payload and mark an
   arbitrary payment as paid).
2. Checkout falls back to demo mode when STRIPE_SECRET_KEY is unset, so the
   platform still works end-to-end without a Stripe account.
"""
from datetime import date, timedelta

from tests.helpers import auth_headers, make_freelancer, register


def test_stripe_webhook_rejected_without_configured_secret(client):
    resp = client.post(
        "/api/webhooks/stripe",
        json={"type": "checkout.session.completed", "data": {"object": {"id": "cs_fake"}}},
    )
    assert resp.status_code == 503


def test_stripe_webhook_rejects_forged_signature(client, monkeypatch):
    """Even if a secret WERE configured, a request with a bad/missing
    signature header must be rejected — this is the actual anti-forgery check."""
    import app.routes.webhooks as webhooks_module

    monkeypatch.setattr(webhooks_module.settings, "STRIPE_WEBHOOK_SECRET", "whsec_test_secret")
    resp = client.post(
        "/api/webhooks/stripe",
        json={"type": "checkout.session.completed", "data": {"object": {"id": "cs_fake"}}},
        headers={"stripe-signature": "t=1,v1=not-a-real-signature"},
    )
    assert resp.status_code == 400


def test_payments_config_reports_stripe_disabled_by_default(client):
    resp = client.get("/api/payments/config")
    assert resp.status_code == 200
    assert resp.json()["stripe_enabled"] is False


def test_checkout_requires_milestone_in_review(client):
    freelancer = make_freelancer(
        client,
        bio="SEO and social media marketing specialist, ads and campaigns",
        skills=["marketing", "seo"],
    )
    freelancer_id = freelancer["user"]["id"]
    f_token = freelancer["access_token"]

    client_data = register(client, "client")
    c_token = client_data["access_token"]

    job = client.post("/api/jobs", headers=auth_headers(c_token), json={
        "title": "SEO campaign for online store",
        "description": "Need marketing help: SEO, ads, social media campaign for our shop.",
        "budget": 1500,
        "deadline": str(date.today() + timedelta(days=14)),
    }).json()

    matches = client.get(f"/api/matches/job/{job['id']}", headers=auth_headers(c_token)).json()
    match = next(m for m in matches if m["freelancer_id"] == freelancer_id)
    contract = client.post(f"/api/matches/{match['id']}/accept", headers=auth_headers(f_token)).json()
    milestone_id = contract["milestones"][0]["id"]

    # Milestone is still "pending" (not submitted yet) — checkout must reject it.
    resp = client.post(
        f"/api/payments/checkout/{contract['id']}/{milestone_id}",
        headers=auth_headers(c_token),
    )
    assert resp.status_code == 400

    # Only the client (payer) may initiate checkout, not the freelancer.
    resp = client.post(
        f"/api/payments/checkout/{contract['id']}/{milestone_id}",
        headers=auth_headers(f_token),
    )
    assert resp.status_code == 403
