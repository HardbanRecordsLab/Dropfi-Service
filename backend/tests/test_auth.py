from tests.helpers import auth_headers, register, unique_email


def test_register_client_and_freelancer(client):
    client_data = register(client, "client")
    assert client_data["user"]["role"] == "client"
    assert client_data["access_token"]

    freelancer_data = register(client, "freelancer")
    assert freelancer_data["user"]["role"] == "freelancer"
    assert freelancer_data["user"]["referral_code"]


def test_duplicate_email_rejected(client):
    email = unique_email("dup")
    register(client, "client", email=email)
    resp = client.post("/api/auth/register", json={
        "email": email, "password": "testpass123", "role": "client",
    })
    assert resp.status_code == 400


def test_login_wrong_password_rejected(client):
    email = unique_email("login")
    register(client, "client", email=email)
    resp = client.post("/api/auth/login", json={"email": email, "password": "wrong-password"})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client):
    data = register(client, "client")
    resp = client.get("/api/auth/me", headers=auth_headers(data["access_token"]))
    assert resp.status_code == 200
    assert resp.json()["email"] == data["user"]["email"]


def test_referral_code_links_referrer(client):
    referrer = register(client, "freelancer")
    referred = register(client, "client", referral_code=referrer["user"]["referral_code"])
    assert referred["user"]["email"]
    resp = client.get("/api/referrals/me", headers=auth_headers(referrer["access_token"]))
    assert resp.status_code == 200
    assert resp.json()["referred_count"] == 1
