from datetime import date, timedelta

from tests.helpers import auth_headers, make_freelancer, register


def _future(days: int) -> str:
    return str(date.today() + timedelta(days=days))


def test_full_escrow_flow_in_demo_mode(client):
    """End-to-end: job -> AI match -> accept -> contract+milestones -> submit ->
    Stripe checkout (demo mode, no STRIPE_SECRET_KEY) -> release -> auto-complete
    -> AI-generated agreement download. This is the platform's core money loop."""
    freelancer = make_freelancer(
        client,
        bio="Experienced web developer, e-commerce integrations, WordPress and React",
        skills=["web development", "e-commerce"],
        location="Krakow",
        first_name="Marek",
        last_name="Nowak",
    )
    freelancer_id = freelancer["user"]["id"]
    f_token = freelancer["access_token"]

    client_data = register(client, "client", first_name="Ola", last_name="Zielinska")
    c_token = client_data["access_token"]

    job = client.post("/api/jobs", headers=auth_headers(c_token), json={
        "title": "WooCommerce store integration",
        "description": "Need a developer to integrate our WooCommerce store, coding required, react frontend.",
        "budget": 4000,
        "deadline": _future(14),
        "location": "Krakow",
    }).json()

    matches = client.get(f"/api/matches/job/{job['id']}", headers=auth_headers(c_token)).json()
    match = next(m for m in matches if m["freelancer_id"] == freelancer_id)

    accept_resp = client.post(f"/api/matches/{match['id']}/accept", headers=auth_headers(f_token))
    assert accept_resp.status_code == 200, accept_resp.text
    contract = accept_resp.json()
    assert contract["status"] == "in_progress"
    assert len(contract["milestones"]) >= 2
    contract_id = contract["id"]

    # Walk every milestone in order: freelancer submits, client pays (demo) + releases.
    milestone_count = len(contract["milestones"])
    for _ in range(milestone_count):
        current = client.get(f"/api/contracts/{contract_id}", headers=auth_headers(c_token)).json()
        pending = next(m for m in current["milestones"] if m["status"] == "pending")

        submit = client.post(
            f"/api/contracts/{contract_id}/milestones/{pending['id']}/submit",
            headers=auth_headers(f_token),
        )
        assert submit.status_code == 200, submit.text

        checkout = client.post(
            f"/api/payments/checkout/{contract_id}/{pending['id']}",
            headers=auth_headers(c_token),
        )
        assert checkout.status_code == 200
        assert checkout.json()["mode"] == "demo", "no STRIPE_SECRET_KEY in tests -> must fall back to demo mode"

        release = client.post(
            f"/api/contracts/{contract_id}/milestones/{pending['id']}/release",
            headers=auth_headers(c_token),
        )
        assert release.status_code == 200, release.text

    final = client.get(f"/api/contracts/{contract_id}", headers=auth_headers(c_token)).json()
    assert final["status"] == "completed"
    assert final["released_amount"] == final["amount"]

    agreement = client.get(
        f"/api/contracts/{contract_id}/agreement?language=en",
        headers=auth_headers(c_token),
    )
    assert agreement.status_code == 200
    assert "SERVICE AGREEMENT" in agreement.json()["agreement"]


def test_refund_guarantee_available_only_after_no_show_window(client):
    freelancer = make_freelancer(
        client,
        bio="Graphic designer, logos and branding, figma expert",
        skills=["graphic design"],
        first_name="Kasia",
        last_name="Wozniak",
    )
    freelancer_id = freelancer["user"]["id"]
    f_token = freelancer["access_token"]

    client_data = register(client, "client")
    c_token = client_data["access_token"]

    job = client.post("/api/jobs", headers=auth_headers(c_token), json={
        "title": "Logo and branding package",
        "description": "Need a designer for a full logo and branding package, figma files required.",
        "budget": 2500,
        "deadline": _future(14),
    }).json()

    matches = client.get(f"/api/matches/job/{job['id']}", headers=auth_headers(c_token)).json()
    match = next(m for m in matches if m["freelancer_id"] == freelancer_id)
    contract = client.post(f"/api/matches/{match['id']}/accept", headers=auth_headers(f_token)).json()

    detail = client.get(f"/api/contracts/{contract['id']}", headers=auth_headers(c_token)).json()
    assert detail["refund_eligible"] is False, "no-show refund should not be available immediately"

    refund_resp = client.post(f"/api/contracts/{contract['id']}/request-refund", headers=auth_headers(c_token))
    assert refund_resp.status_code == 400
