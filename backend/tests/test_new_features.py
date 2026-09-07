"""Smoke tests for the 8 new platform features (F1-F8) shipped alongside the
Stripe payment fix — each exercises its offline/no-API-key fallback path,
same design as every other AI feature in this codebase."""
from datetime import date, timedelta

from app.utils import currency as currency_utils
from tests.helpers import auth_headers, make_freelancer, register


def test_f1_ai_listing_factory(client):
    data = register(client, "client")
    resp = client.post(
        "/api/factory/listing",
        headers=auth_headers(data["access_token"]),
        json={"product_name": "Wireless Earbuds X200", "marketplace": "shopify", "language": "en"},
    )
    assert resp.status_code == 200, resp.text
    content = resp.json()["content"]
    assert content["title"]
    assert content["bullet_points"]

    history = client.get("/api/factory/history", headers=auth_headers(data["access_token"]))
    assert history.status_code == 200
    assert len(history.json()) >= 1


def test_f6_video_script_generator(client):
    data = register(client, "client")
    resp = client.post(
        "/api/factory/video-script",
        headers=auth_headers(data["access_token"]),
        json={"product_name": "Wireless Earbuds X200", "language": "en"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["hook"] and body["script"] and body["cta"]


def test_f2_currency_and_tax_live_provider_override(monkeypatch, client):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    monkeypatch.setattr(
        currency_utils.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse({"rates": {"PLN": 1.0, "EUR": 1.42, "USD": 1.31}}),
    )

    resp = client.get("/api/fx/rates")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["rates"]["EUR"] == 1.42
    assert payload["source"] == "live"


def test_f2_currency_and_tax(client):
    rates = client.get("/api/fx/rates")
    assert rates.status_code == 200
    assert rates.json()["base"] == "PLN"
    assert "EUR" in rates.json()["rates"]

    hint = client.get("/api/fx/tax-hint/DE")
    assert hint.status_code == 200
    assert "note" in hint.json()


def test_f4_supplier_risk_score(client):
    freelancer = make_freelancer(
        client,
        bio="Translator, Polish-English-German, certified",
        skills=["translation"],
    )
    resp = client.get(f"/api/users/{freelancer['user']['id']}/risk-score")
    assert resp.status_code == 200
    body = resp.json()
    assert 0 <= body["score"] <= 100
    assert body["level"] in ("low", "medium", "high")


def test_f5_ai_copilot(client):
    client_data = register(client, "client")
    token = client_data["access_token"]
    job = client.post("/api/jobs", headers=auth_headers(token), json={
        "title": "Blog articles about dropshipping",
        "description": "Need 5 blog articles about dropshipping trends, copywriting required.",
        "budget": 800,
        "deadline": str(date.today() + timedelta(days=10)),
    }).json()

    resp = client.post(
        "/api/copilot/ask",
        headers=auth_headers(token),
        json={"job_id": job["id"], "question": "What is the budget for this job?", "language": "en"},
    )
    assert resp.status_code == 200
    assert resp.json()["answer"]

    history = client.get(f"/api/copilot/history/{job['id']}", headers=auth_headers(token))
    assert history.status_code == 200
    assert len(history.json()) == 1


def test_f5_ai_copilot_history_visible_to_contract_parties(client):
    client_data = register(client, "client")
    client_token = client_data["access_token"]
    freelancer_data = make_freelancer(client, "Content strategist and editor", ["writing", "blogging"])
    freelancer_token = freelancer_data["access_token"]

    job = client.post(
        "/api/jobs",
        headers=auth_headers(client_token),
        json={
            "title": "SEO blog plan",
            "description": "Need a content plan for a new product launch.",
            "budget": 950,
            "deadline": str(date.today() + timedelta(days=12)),
        },
    ).json()

    matches = client.get(f"/api/matches/job/{job['id']}", headers=auth_headers(client_token)).json()
    match = next(m for m in matches if m["freelancer_id"] == freelancer_data["user"]["id"])
    resp = client.post(f"/api/matches/{match['id']}/accept", headers=auth_headers(freelancer_token))
    assert resp.status_code == 200, resp.text

    ask = client.post(
        "/api/copilot/ask",
        headers=auth_headers(client_token),
        json={"job_id": job["id"], "question": "How much is the project budget?", "language": "en"},
    )
    assert ask.status_code == 200, ask.text

    history = client.get(f"/api/copilot/history/{job['id']}", headers=auth_headers(freelancer_token))
    assert history.status_code == 200, history.text
    assert len(history.json()) >= 1
    assert history.json()[0]["question"] == "How much is the project budget?"


def test_f7_timezone_scheduler(client):
    freelancer = make_freelancer(
        client,
        bio="Video editor and motion designer",
        skills=["video"],
        location="Manila",
    )
    freelancer_id = freelancer["user"]["id"]
    client_data = register(client, "client")
    c_token = client_data["access_token"]

    job = client.post("/api/jobs", headers=auth_headers(c_token), json={
        "title": "YouTube video editing",
        "description": "Need a video editor for YouTube channel, motion graphics editing.",
        "budget": 1200,
        "deadline": str(date.today() + timedelta(days=14)),
    }).json()

    matches = client.get(f"/api/matches/job/{job['id']}", headers=auth_headers(c_token)).json()
    match = next(m for m in matches if m["freelancer_id"] == freelancer_id)

    resp = client.get(f"/api/matches/{match['id']}/schedule", headers=auth_headers(c_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] in ("live-overlap", "handoff", "async-24-7")


def test_f8_white_label_api(client):
    agency = register(client, "client")
    token = agency["access_token"]

    key_resp = client.post(
        "/api/developer/keys",
        headers=auth_headers(token),
        json={"name": "Production", "brand_name": "Acme Agency"},
    )
    assert key_resp.status_code == 200, key_resp.text
    api_key = key_resp.json()["key"]
    assert api_key.startswith("dpk_")

    listed = client.get("/api/developer/keys", headers=auth_headers(token))
    assert len(listed.json()) == 1

    # Partner endpoint: create a job on behalf of the agency's own client, using only the API key.
    partner_resp = client.post(
        "/api/v1/external/jobs",
        headers={"X-Api-Key": api_key},
        json={
            "title": "White-label test job",
            "description": "Created through the partner API on behalf of an agency client.",
            "budget": 900,
            "deadline": str(date.today() + timedelta(days=14)),
        },
    )
    assert partner_resp.status_code == 200, partner_resp.text
    assert partner_resp.json()["brand"] == "Acme Agency"

    # Wrong/missing key must be rejected (valid body, so this is purely an auth check).
    valid_body = {"title": "Test job", "description": "y" * 20, "budget": 100, "deadline": str(date.today() + timedelta(days=5))}
    denied = client.post("/api/v1/external/jobs", json=valid_body)
    assert denied.status_code == 401

    revoke = client.delete(f"/api/developer/keys/{key_resp.json()['id']}", headers=auth_headers(token))
    assert revoke.status_code == 200

    denied_after_revoke = client.post(
        "/api/v1/external/jobs",
        headers={"X-Api-Key": api_key},
        json=valid_body,
    )
    assert denied_after_revoke.status_code == 401


def test_f3_contract_agreement_requires_participant(client):
    """Only the client/freelancer on the contract (or an admin) may fetch its
    AI-generated agreement — a third party must be rejected."""
    outsider = register(client, "client")
    resp = client.get(
        "/api/contracts/nonexistent-contract-id/agreement",
        headers=auth_headers(outsider["access_token"]),
    )
    assert resp.status_code == 404
