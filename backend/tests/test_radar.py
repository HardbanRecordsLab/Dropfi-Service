"""Portal Radar: connector normalisation, dedup upsert, lead import → AI
matching, permissions. No real network — connector fetch methods are stubbed."""
import os

from app.connectors import registry
from app.connectors.base import NormalizedListing, NormalizedTalent
from tests.helpers import auth_headers, make_freelancer, register


def _admin_token(client):
    resp = client.post("/api/auth/login", json={
        "email": os.environ["ADMIN_EMAIL"], "password": os.environ["ADMIN_PASSWORD"],
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _stub_source(monkeypatch, slug, *, listings=None, talent=None, boom=False):
    conn = registry.get(slug)
    assert conn is not None

    def _listings(limit):
        if boom:
            raise RuntimeError("source exploded")
        return listings or []

    def _talent(limit):
        if boom:
            raise RuntimeError("source exploded")
        return talent or []

    monkeypatch.setattr(conn, "fetch_listings", _listings)
    monkeypatch.setattr(conn, "fetch_talent", _talent)


def test_scan_upserts_and_dedupes(client, monkeypatch):
    listing = NormalizedListing(
        external_id="job-1", url="https://example.com/job-1",
        title="Need a Shopify product photographer",
        description="100 white-background product photos, clothing.",
        company="Acme", tags=["photography", "retouching"], is_remote=True,
        category="Photography",
    )
    _stub_source(monkeypatch, "remotive", listings=[listing])

    admin = _admin_token(client)
    r1 = client.post("/api/radar/scan?source=remotive", headers=auth_headers(admin))
    assert r1.status_code == 200, r1.text

    rows = client.get("/api/radar/listings?source=remotive", headers=auth_headers(admin)).json()
    assert len(rows) == 1
    assert rows[0]["title"].startswith("Need a Shopify")
    assert rows[0]["status"] == "new"

    # second scan of the same external_id must not create a duplicate
    client.post("/api/radar/scan?source=remotive", headers=auth_headers(admin))
    rows2 = client.get("/api/radar/listings?source=remotive", headers=auth_headers(admin)).json()
    assert len(rows2) == 1


def test_one_broken_source_does_not_abort_others(client, monkeypatch):
    good = NormalizedListing(external_id="ok-1", url="https://example.com/ok-1", title="Fine job")
    _stub_source(monkeypatch, "jobicy", listings=[good])
    _stub_source(monkeypatch, "arbeitnow", boom=True)

    admin = _admin_token(client)
    res = client.post("/api/radar/scan?source=arbeitnow", headers=auth_headers(admin)).json()
    # inline path returns the log dict; queued path returns status only
    if res.get("status") == "done":
        assert res["result"]["ok"] is False

    client.post("/api/radar/scan?source=jobicy", headers=auth_headers(admin))
    rows = client.get("/api/radar/listings?source=jobicy", headers=auth_headers(admin)).json()
    assert any(r["external_id"] == "ok-1" for r in rows)

    sources = client.get("/api/radar/sources", headers=auth_headers(admin)).json()
    arbeitnow = next(s for s in sources if s["slug"] == "arbeitnow")
    assert arbeitnow["last_scan_ok"] is False


def test_import_listing_creates_job_and_matches(client, monkeypatch):
    make_freelancer(client, "Product and fashion photographer, retouching, white background",
                    ["photography", "retouching"], location="Warsaw")

    listing = NormalizedListing(
        external_id="imp-1", url="https://example.com/imp-1",
        title="Product photographer for 80 photos",
        description="White background product photography, clothing and accessories.",
        company="ShopX", tags=["photography"], budget_max=2000.0, category="Photography",
    )
    _stub_source(monkeypatch, "remoteok", listings=[listing])

    admin = _admin_token(client)
    client.post("/api/radar/scan?source=remoteok", headers=auth_headers(admin))
    row = client.get("/api/radar/listings?source=remoteok", headers=auth_headers(admin)).json()[0]

    imp = client.post(f"/api/radar/listings/{row['id']}/import", headers=auth_headers(admin))
    assert imp.status_code == 200, imp.text
    job_id = imp.json()["job_id"]

    job = client.get(f"/api/jobs/{job_id}").json()
    assert job["external_source"] == "remoteok"
    assert job["budget"] == 2000.0

    # re-import is blocked
    again = client.post(f"/api/radar/listings/{row['id']}/import", headers=auth_headers(admin))
    assert again.status_code == 409

    matches = client.get(f"/api/matches/job/{job_id}", headers=auth_headers(admin)).json()
    assert len(matches) >= 1


def test_permissions(client, monkeypatch):
    _stub_source(monkeypatch, "devto", talent=[NormalizedTalent(
        external_id="dev-1", url="https://dev.to/someone", name="Someone", skills=["webdev"],
    )])
    freelancer = register(client, "freelancer")["access_token"]

    # scan is admin-only
    assert client.post("/api/radar/scan?source=devto", headers=auth_headers(freelancer)).status_code == 403

    admin = _admin_token(client)
    client.post("/api/radar/scan?source=devto", headers=auth_headers(admin))
    talent = client.get("/api/radar/talent?source=devto", headers=auth_headers(freelancer)).json()
    assert len(talent) == 1
    tid = talent[0]["id"]

    # freelancer cannot change talent status / import
    assert client.post(f"/api/radar/talent/{tid}/status?status=invited",
                       headers=auth_headers(freelancer)).status_code == 403

    ok = client.post(f"/api/radar/talent/{tid}/status?status=contacted", headers=auth_headers(admin))
    assert ok.status_code == 200 and ok.json()["status"] == "contacted"


def test_stats_endpoint(client):
    freelancer = register(client, "freelancer")["access_token"]
    stats = client.get("/api/radar/stats", headers=auth_headers(freelancer)).json()
    assert stats["sources_total"] == len(registry.ALL_CONNECTORS)
    assert "by_status" in stats["listings"]
