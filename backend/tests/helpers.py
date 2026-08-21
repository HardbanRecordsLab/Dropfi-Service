"""Shared test helpers (not a conftest — imported explicitly by test modules)."""
import uuid

from fastapi.testclient import TestClient


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@test.dropify.app"


def register(client: TestClient, role: str, **extra) -> dict:
    """Register a user via the real /auth/register endpoint. Returns {access_token, user}."""
    email = extra.pop("email", None) or unique_email(role)
    payload = {
        "email": email,
        "password": "testpass123",
        "role": role,
        "first_name": extra.pop("first_name", "Test"),
        "last_name": extra.pop("last_name", role.capitalize()),
        **extra,
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def make_freelancer(client: TestClient, bio: str, skills: list[str], location: str = "", **extra) -> dict:
    """Register a freelancer AND set a profile (bio/skills), which is what
    actually computes+stores the embedding used for AI matching — a
    freelancer with no profile update is invisible to the matching engine."""
    data = register(client, "freelancer", **extra)
    token = data["access_token"]
    resp = client.put("/api/users/me", headers=auth_headers(token), json={
        "bio": bio,
        "skills": skills,
        "location": location,
        "languages": ["Polish", "English"],
    })
    assert resp.status_code == 200, resp.text
    return data
