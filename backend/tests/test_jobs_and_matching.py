from datetime import date, timedelta

from tests.helpers import auth_headers, make_freelancer, register


def _future(days: int) -> str:
    return str(date.today() + timedelta(days=days))


def test_job_creation_triggers_ai_categorization_and_matching(client):
    freelancer = make_freelancer(
        client,
        bio="Professional product photographer specializing in e-commerce photography and retouching",
        skills=["photography", "retouching"],
        location="Warsaw",
    )
    freelancer_id = freelancer["user"]["id"]

    client_data = register(client, "client")
    token = client_data["access_token"]

    resp = client.post("/api/jobs", headers=auth_headers(token), json={
        "title": "100 product photos for e-commerce",
        "description": "We need a professional photographer for 100 product photos with retouching. Warsaw based.",
        "budget": 3500,
        "deadline": _future(14),
        "location": "Warsaw",
    })
    assert resp.status_code == 201, resp.text
    job = resp.json()

    # AI job analysis (rule-based fallback — no ANTHROPIC_API_KEY in tests)
    assert job["category"] == "Photography"
    assert "photography" in job["required_skills"]
    assert job["ai_analysis"]["model"] == "rules"

    matches_resp = client.get(f"/api/matches/job/{job['id']}", headers=auth_headers(token))
    assert matches_resp.status_code == 200
    matches = matches_resp.json()
    assert any(m["freelancer_id"] == freelancer_id for m in matches), (
        "the matching freelancer should have been auto-matched by the AI pipeline"
    )


def test_job_list_filters_by_new_tier2_category(client):
    client_data = register(client, "client")
    token = client_data["access_token"]

    resp = client.post("/api/jobs", headers=auth_headers(token), json={
        "title": "Music production for a new single",
        "description": "Need mixing and mastering for one track — produkcja muzyczna.",
        "budget": 2000,
        "deadline": _future(10),
    })
    job = resp.json()
    assert job["category"] == "Music Production"

    filtered = client.get("/api/jobs?category=Music Production").json()
    assert any(j["id"] == job["id"] for j in filtered)


def test_ai_onboarding_generates_job_draft(client):
    client_data = register(client, "client")
    token = client_data["access_token"]
    resp = client.post(
        "/api/jobs/generate",
        headers=auth_headers(token),
        json={"idea": "Need a real estate photographer for a property listing in Warsaw"},
    )
    assert resp.status_code == 200, resp.text
    draft = resp.json()["draft"]
    assert draft["title"]
    assert draft["category"]


def test_recommended_jobs_requires_freelancer_role(client):
    client_data = register(client, "client")
    resp = client.get("/api/jobs/recommended", headers=auth_headers(client_data["access_token"]))
    assert resp.status_code == 403
