"""Password reset, email verification, and dispute-resolution flows."""
from datetime import date, timedelta

from tests.helpers import auth_headers, make_freelancer, register


def test_forgot_password_always_returns_generic_message(client):
    """Must not reveal whether an email is registered (anti-enumeration)."""
    known = register(client, "client")
    known_email = known["user"]["email"]

    resp_known = client.post("/api/auth/forgot-password", json={"email": known_email})
    resp_unknown = client.post("/api/auth/forgot-password", json={"email": "nobody-here@test.dropify.app"})

    assert resp_known.status_code == 200
    assert resp_unknown.status_code == 200
    assert resp_known.json() == resp_unknown.json()


def test_reset_password_full_flow(client, monkeypatch):
    import app.routes.auth as auth_module

    captured = {}

    def _fake_notify_email(to, subject, headline, body, cta_url="", cta_label=""):
        captured["cta_url"] = cta_url

    monkeypatch.setattr(auth_module, "notify_email", _fake_notify_email)

    data = register(client, "client")
    email = data["user"]["email"]

    client.post("/api/auth/forgot-password", json={"email": email})
    assert "token=" in captured["cta_url"]
    token = captured["cta_url"].split("token=")[1]

    reset_resp = client.post("/api/auth/reset-password", json={"token": token, "new_password": "brandnewpass123"})
    assert reset_resp.status_code == 200, reset_resp.text

    old_login = client.post("/api/auth/login", json={"email": email, "password": "testpass123"})
    assert old_login.status_code == 401

    new_login = client.post("/api/auth/login", json={"email": email, "password": "brandnewpass123"})
    assert new_login.status_code == 200


def test_reset_password_rejects_garbage_token(client):
    resp = client.post("/api/auth/reset-password", json={"token": "not-a-real-token", "new_password": "whatever123"})
    assert resp.status_code == 400


def test_purpose_scoped_tokens_cannot_be_used_as_session_tokens(client):
    """A password-reset/email-verify JWT is signed with the same SECRET_KEY as
    a normal access token — decode_token() must still reject it (via its
    'purpose' claim), or a leaked reset-email link would double as a full
    login session for that account."""
    from app.utils.security import create_purpose_token, decode_token

    reset_token = create_purpose_token("some-user-id", "password_reset")
    verify_token = create_purpose_token("some-user-id", "email_verify")
    assert decode_token(reset_token) is None
    assert decode_token(verify_token) is None

    data = register(client, "client")
    resp = client.get("/api/auth/me", headers=auth_headers(
        create_purpose_token(data["user"]["id"], "password_reset")
    ))
    assert resp.status_code == 401


def test_email_verification_flow(client, monkeypatch):
    import app.routes.auth as auth_module

    captured = {}
    monkeypatch.setattr(
        auth_module, "notify_email",
        lambda to, subject, headline, body, cta_url="", cta_label="": captured.__setitem__("cta_url", cta_url),
    )

    data = register(client, "client")
    token_val = data["access_token"]
    me = client.get("/api/auth/me", headers=auth_headers(token_val)).json()
    assert me["email_verified"] is False

    resend = client.post("/api/auth/send-verification", headers=auth_headers(token_val))
    assert resend.status_code == 200
    verify_token = captured["cta_url"].split("token=")[1]

    verify_resp = client.post("/api/auth/verify-email", json={"token": verify_token})
    assert verify_resp.status_code == 200

    me_after = client.get("/api/auth/me", headers=auth_headers(token_val)).json()
    assert me_after["email_verified"] is True


def test_verify_email_rejects_garbage_token(client):
    resp = client.post("/api/auth/verify-email", json={"token": "garbage"})
    assert resp.status_code == 400


def _make_disputable_contract(client) -> tuple[dict, dict, dict]:
    freelancer = make_freelancer(
        client,
        bio="Copywriter and content strategist, blog articles and SEO copy",
        skills=["copywriting"],
    )
    client_data = register(client, "client")
    c_token = client_data["access_token"]

    job = client.post("/api/jobs", headers=auth_headers(c_token), json={
        "title": "Blog content package",
        "description": "Need 10 blog articles, copywriting and content strategy required.",
        "budget": 2000,
        "deadline": str(date.today() + timedelta(days=14)),
    }).json()

    matches = client.get(f"/api/matches/job/{job['id']}", headers=auth_headers(c_token)).json()
    match = next(m for m in matches if m["freelancer_id"] == freelancer["user"]["id"])
    contract = client.post(f"/api/matches/{match['id']}/accept", headers=auth_headers(freelancer["access_token"])).json()
    return freelancer, client_data, contract


def test_dispute_raise_and_admin_release_to_freelancer(client):
    freelancer, client_data, contract = _make_disputable_contract(client)

    dispute_resp = client.post(
        f"/api/contracts/{contract['id']}/dispute",
        headers=auth_headers(client_data["access_token"]),
        json={"reason": "The freelancer has not delivered anything after a week.", "language": "en"},
    )
    assert dispute_resp.status_code == 200, dispute_resp.text
    disputed = dispute_resp.json()
    assert disputed["status"] == "disputed"
    assert disputed["dispute_raised_by"] == "client"
    assert disputed["dispute_ai_assessment"]

    # Non-admin cannot resolve
    denied = client.post(
        f"/api/contracts/{contract['id']}/resolve-dispute",
        headers=auth_headers(client_data["access_token"]),
        json={"resolution": "release_to_freelancer"},
    )
    assert denied.status_code == 403

    admin_token = client.post("/api/auth/login", json={"email": "admin@dropify.app", "password": "admin-test-123"}).json()["access_token"]

    listed = client.get("/api/admin/disputes", headers=auth_headers(admin_token)).json()
    assert any(d["id"] == contract["id"] for d in listed)

    resolved = client.post(
        f"/api/contracts/{contract['id']}/resolve-dispute",
        headers=auth_headers(admin_token),
        json={"resolution": "release_to_freelancer"},
    )
    assert resolved.status_code == 200, resolved.text
    body = resolved.json()
    assert body["status"] == "completed"
    assert body["dispute_resolution"] == "release_to_freelancer"
    assert body["released_amount"] == body["amount"]


def test_dispute_raise_and_admin_refund_client(client):
    freelancer, client_data, contract = _make_disputable_contract(client)

    client.post(
        f"/api/contracts/{contract['id']}/dispute",
        headers=auth_headers(freelancer["access_token"]),
        json={"reason": "The client changed the scope after I already started.", "language": "en"},
    )

    admin_token = client.post("/api/auth/login", json={"email": "admin@dropify.app", "password": "admin-test-123"}).json()["access_token"]
    resolved = client.post(
        f"/api/contracts/{contract['id']}/resolve-dispute",
        headers=auth_headers(admin_token),
        json={"resolution": "refund_client"},
    )
    assert resolved.status_code == 200, resolved.text
    body = resolved.json()
    assert body["status"] == "cancelled"
    assert body["dispute_resolution"] == "refund_client"

    # The job should be reopened for new candidates.
    job = client.get(f"/api/jobs/{contract['job_id']}").json()
    assert job["status"] == "open"


def test_cannot_dispute_a_contract_twice_without_resolution(client):
    _, client_data, contract = _make_disputable_contract(client)
    client.post(
        f"/api/contracts/{contract['id']}/dispute",
        headers=auth_headers(client_data["access_token"]),
        json={"reason": "First dispute reason, long enough to pass validation.", "language": "en"},
    )
    second = client.post(
        f"/api/contracts/{contract['id']}/dispute",
        headers=auth_headers(client_data["access_token"]),
        json={"reason": "Second dispute reason, long enough to pass validation.", "language": "en"},
    )
    assert second.status_code == 400
