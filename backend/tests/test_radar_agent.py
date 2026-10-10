"""HRL Digital sales agent (Portal Radar steps 1-7): fit scoring, offer
drafts, pipeline/stats, auto-score-and-alert dedupe, and migration
idempotency. No network, no LLM key (see conftest.py) — exercises the
rule-based fallback paths exactly like a fresh deployment with no
OPENROUTER_API_KEY configured yet.
"""
import importlib.util
import json
import os
from pathlib import Path

import pytest
import sqlalchemy as sa

import app.utils.agency_profile as agency_profile_mod
from app.connectors import registry
from app.connectors.base import NormalizedListing
from app.utils.ai import generate_offer
from app.utils.radar_scoring import score_listing
from tests.helpers import auth_headers, register


def _admin_token(client):
    resp = client.post("/api/auth/login", json={
        "email": os.environ["ADMIN_EMAIL"], "password": os.environ["ADMIN_PASSWORD"],
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture(autouse=True)
def _reset_agency_profile_cache():
    """load_agency_profile() caches at module scope; several tests here point
    AGENCY_PROFILE_PATH at a tmp_path file, so the cache must not leak into
    other tests in this file or into the rest of the (session-scoped) suite."""
    agency_profile_mod._cache = None
    yield
    agency_profile_mod._cache = None


REAL_PROFILE = {
    "agency_name": "HRL Digital",
    "tagline": "Strony WWW i aplikacje webowe dla firm",
    "services": [
        {"name": "Strona WWW", "description": "Strony firmowe, landing page, CMS",
         "price_from_pln": 2000, "typical_timeline": "2-3 tygodnie"},
    ],
    "keywords_include": ["strona www", "website", "landing page"],
    "keywords_exclude": ["logo"],
    "min_budget_pln": 1000,
    "languages": ["pl", "en"],
    "portfolio": [{"title": "Przykład", "url": "https://example.com", "one_liner": "Strona firmowa"}],
    "tone": "rzeczowy",
    "signature": "Kamil, HRL Digital",
}


def _write_real_profile(monkeypatch, tmp_path, overrides=None):
    data = {**REAL_PROFILE, **(overrides or {})}
    path = tmp_path / "agency_profile.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr("app.config.settings.AGENCY_PROFILE_PATH", str(path))
    agency_profile_mod._cache = None


def _force_template_profile(monkeypatch, tmp_path):
    """Points AGENCY_PROFILE_PATH at a file that doesn't exist, so
    load_agency_profile() falls back to the committed example template
    (is_template=True) — regardless of whether a real, filled-in
    agency_profile.json happens to sit at the default path on this machine."""
    monkeypatch.setattr("app.config.settings.AGENCY_PROFILE_PATH", str(tmp_path / "does-not-exist.json"))
    agency_profile_mod._cache = None


class _FakeListing:
    """Mimics the subset of ExternalListing's attributes score_listing() /
    generate_offer() read — avoids needing a DB row for pure-function tests."""

    def __init__(self, **kw):
        self.title = kw.get("title", "")
        self.description = kw.get("description", "")
        self.category = kw.get("category", "")
        self.tags = kw.get("tags", [])
        self.budget_min = kw.get("budget_min")
        self.budget_max = kw.get("budget_max")
        self.budget_text = kw.get("budget_text", "")
        self.language = kw.get("language", "pl")
        self.posted_at = kw.get("posted_at")


# ---------------------------------------------------------------------------
# Scoring (pure function, step 3)
# ---------------------------------------------------------------------------

def test_score_listing_excludes_keyword_hit():
    listing = _FakeListing(title="Potrzebuję nowego logo dla firmy", description="Projekt logo i identyfikacji")
    score, reason = score_listing(listing, REAL_PROFILE)
    assert score == 0
    assert "wyklucz" in reason.lower()


def test_score_listing_rewards_include_keyword_match():
    good = _FakeListing(title="Potrzebuję strony WWW dla firmy", description="Landing page, nowoczesny design",
                         budget_max=5000, language="pl")
    unrelated = _FakeListing(title="Potrzebuję grafika do social media", description="5 postów na Instagram",
                              budget_max=5000, language="pl")
    good_score, _ = score_listing(good, REAL_PROFILE)
    unrelated_score, _ = score_listing(unrelated, REAL_PROFILE)
    assert good_score > unrelated_score


def test_score_listing_penalizes_budget_below_minimum():
    high_budget = _FakeListing(title="Strona WWW", description="landing page", budget_max=5000, language="pl")
    low_budget = _FakeListing(title="Strona WWW", description="landing page", budget_max=100, language="pl")
    high_score, _ = score_listing(high_budget, REAL_PROFILE)
    low_score, _ = score_listing(low_budget, REAL_PROFILE)
    assert high_score > low_score


def test_score_listing_penalizes_unsupported_language():
    pl = _FakeListing(title="Strona WWW", description="landing page", budget_max=5000, language="pl")
    de = _FakeListing(title="Strona WWW", description="landing page", budget_max=5000, language="de")
    pl_score, _ = score_listing(pl, REAL_PROFILE)
    de_score, _ = score_listing(de, REAL_PROFILE)
    assert pl_score > de_score


# ---------------------------------------------------------------------------
# Offer generation — fallback mode (step 4; no OPENROUTER_API_KEY in tests)
# ---------------------------------------------------------------------------

def test_generate_offer_fallback_mode_polish():
    listing = _FakeListing(title="Potrzebuję strony WWW dla małej firmy",
                            description="Landing page, mały budżet", budget_max=3000, language="pl")
    result = generate_offer(listing, REAL_PROFILE)
    assert result["source"] == "fallback"
    assert result["offer_language"] == "pl"
    assert result["offer_text"] and len(result["offer_text"]) <= 1800
    assert result["price_min"] is not None and result["price_max"] is not None
    assert len(result["questions"]) >= 2


def test_generate_offer_fallback_mode_english():
    listing = _FakeListing(title="I need a new website for my shop",
                            description="Landing page, small budget", budget_max=3000, language="en")
    result = generate_offer(listing, REAL_PROFILE)
    assert result["source"] == "fallback"
    assert result["offer_language"] == "en"
    assert "Hi" in result["offer_text"] or "website" in result["offer_text"].lower()


# ---------------------------------------------------------------------------
# Offer endpoint — 409 on template profile, 403 for non-admin (step 4)
# ---------------------------------------------------------------------------

def test_offer_endpoint_409_on_template_profile(client, monkeypatch, tmp_path):
    _force_template_profile(monkeypatch, tmp_path)
    conn = registry.get("remotive")
    monkeypatch.setattr(conn, "fetch_listings", lambda limit: [NormalizedListing(
        external_id="agent-offer-409", url="https://example.com/agent-offer-409",
        title="Potrzebuję strony WWW", description="Landing page", budget_max=4000.0,
    )])
    admin = _admin_token(client)
    client.post("/api/radar/scan?source=remotive", headers=auth_headers(admin))
    row = next(r for r in client.get("/api/radar/listings?source=remotive",
                                      headers=auth_headers(admin)).json()
               if r["external_id"] == "agent-offer-409")

    resp = client.post(f"/api/radar/listings/{row['id']}/offer", headers=auth_headers(admin))
    assert resp.status_code == 409


def test_offer_endpoint_forbidden_for_non_admin(client, monkeypatch):
    conn = registry.get("jobicy")
    monkeypatch.setattr(conn, "fetch_listings", lambda limit: [NormalizedListing(
        external_id="agent-offer-403", url="https://example.com/agent-offer-403",
        title="X", description="Y",
    )])
    admin = _admin_token(client)
    client.post("/api/radar/scan?source=jobicy", headers=auth_headers(admin))
    row = next(r for r in client.get("/api/radar/listings?source=jobicy",
                                      headers=auth_headers(admin)).json()
               if r["external_id"] == "agent-offer-403")

    freelancer = register(client, "freelancer")["access_token"]
    resp = client.post(f"/api/radar/listings/{row['id']}/offer", headers=auth_headers(freelancer))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Pipeline transitions + stats (step 5)
# ---------------------------------------------------------------------------

def test_pipeline_won_requires_amount(client, monkeypatch):
    conn = registry.get("remotive")
    monkeypatch.setattr(conn, "fetch_listings", lambda limit: [NormalizedListing(
        external_id="agent-pipeline-noamount", url="https://example.com/agent-pipeline-noamount",
        title="Test", description="Test", budget_max=3000.0,
    )])
    admin = _admin_token(client)
    client.post("/api/radar/scan?source=remotive", headers=auth_headers(admin))
    row = next(r for r in client.get("/api/radar/listings?source=remotive",
                                      headers=auth_headers(admin)).json()
               if r["external_id"] == "agent-pipeline-noamount")

    resp = client.post(f"/api/radar/listings/{row['id']}/pipeline",
                        json={"status": "won"}, headers=auth_headers(admin))
    assert resp.status_code == 422


def test_pipeline_full_transition_updates_stats(client, monkeypatch):
    conn = registry.get("remotive")
    monkeypatch.setattr(conn, "fetch_listings", lambda limit: [NormalizedListing(
        external_id="agent-pipeline-full", url="https://example.com/agent-pipeline-full",
        title="Test", description="Test", budget_max=3000.0,
    )])
    admin = _admin_token(client)
    client.post("/api/radar/scan?source=remotive", headers=auth_headers(admin))
    row = next(r for r in client.get("/api/radar/listings?source=remotive",
                                      headers=auth_headers(admin)).json()
               if r["external_id"] == "agent-pipeline-full")

    r1 = client.post(f"/api/radar/listings/{row['id']}/pipeline",
                      json={"status": "applied"}, headers=auth_headers(admin))
    assert r1.status_code == 200 and r1.json()["applied_at"] is not None

    r2 = client.post(f"/api/radar/listings/{row['id']}/pipeline",
                      json={"status": "replied", "note": "odpisali"}, headers=auth_headers(admin))
    assert r2.status_code == 200
    assert r2.json()["replied_at"] is not None
    assert r2.json()["pipeline_note"] == "odpisali"

    r3 = client.post(f"/api/radar/listings/{row['id']}/pipeline",
                      json={"status": "won", "amount_pln": 4500}, headers=auth_headers(admin))
    assert r3.status_code == 200
    body = r3.json()
    assert body["pipeline"] == "won"
    assert body["won_amount_pln"] == 4500
    assert body["closed_at"] is not None

    stats = client.get("/api/radar/stats", headers=auth_headers(admin)).json()
    sa_stats = stats["sales_agent"]
    assert sa_stats["pipeline"].get("won", 0) >= 1
    assert sa_stats["sent_total"] >= 1
    assert sa_stats["won_total_pln"] >= 4500
    assert 0.0 <= sa_stats["reply_rate"] <= 1.0
    assert 0.0 <= sa_stats["win_rate"] <= 1.0


def test_pipeline_forbidden_for_non_admin(client, monkeypatch):
    conn = registry.get("jobicy")
    monkeypatch.setattr(conn, "fetch_listings", lambda limit: [NormalizedListing(
        external_id="agent-pipeline-403", url="https://example.com/agent-pipeline-403",
        title="X", description="Y",
    )])
    admin = _admin_token(client)
    client.post("/api/radar/scan?source=jobicy", headers=auth_headers(admin))
    row = next(r for r in client.get("/api/radar/listings?source=jobicy",
                                      headers=auth_headers(admin)).json()
               if r["external_id"] == "agent-pipeline-403")

    freelancer = register(client, "freelancer")["access_token"]
    resp = client.post(f"/api/radar/listings/{row['id']}/pipeline",
                        json={"status": "applied"}, headers=auth_headers(freelancer))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Auto score-and-alert after scan, with dedupe (step 6)
# ---------------------------------------------------------------------------

def test_scan_scores_but_does_not_alert_on_template_profile(client, monkeypatch, tmp_path):
    _force_template_profile(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr("app.utils.n8n.notify_n8n", lambda event, payload: calls.append((event, payload)))

    conn = registry.get("remotive")
    monkeypatch.setattr(conn, "fetch_listings", lambda limit: [NormalizedListing(
        external_id="agent-autoscan-template", url="https://example.com/agent-autoscan-template",
        title="Potrzebuję strony WWW dla firmy", description="Landing page", budget_max=9000.0,
    )])
    admin = _admin_token(client)
    client.post("/api/radar/scan?source=remotive", headers=auth_headers(admin))

    row = next(r for r in client.get("/api/radar/listings?source=remotive",
                                      headers=auth_headers(admin)).json()
               if r["external_id"] == "agent-autoscan-template")
    assert row["fit_score"] is not None   # scoring runs regardless of profile state
    assert row["alerted_at"] is None      # but template profile blocks any alert/offer
    assert [c for c in calls if c[1]["id"] == row["id"]] == []


def test_scan_alerts_once_with_real_profile_and_dedupes_on_rescan(client, monkeypatch, tmp_path):
    _write_real_profile(monkeypatch, tmp_path)
    monkeypatch.setattr("app.config.settings.RADAR_ALERT_MIN_SCORE", 1)

    calls = []
    monkeypatch.setattr("app.utils.n8n.notify_n8n", lambda event, payload: calls.append((event, payload)))

    conn = registry.get("jobicy")
    monkeypatch.setattr(conn, "fetch_listings", lambda limit: [NormalizedListing(
        external_id="agent-autoscan-real", url="https://example.com/agent-autoscan-real",
        title="Potrzebuję strony WWW dla firmy", description="Strona firmowa, landing page",
        budget_max=9000.0,
    )])
    admin = _admin_token(client)
    client.post("/api/radar/scan?source=jobicy", headers=auth_headers(admin))

    row = next(r for r in client.get("/api/radar/listings?source=jobicy",
                                      headers=auth_headers(admin)).json()
               if r["external_id"] == "agent-autoscan-real")
    assert row["fit_score"] is not None
    assert row["alerted_at"] is not None
    assert row["offer_text"]

    matching = [c for c in calls if c[1]["id"] == row["id"]]
    assert len(matching) == 1
    assert matching[0][0] == "radar-lead"
    assert matching[0][1]["fit_score"] == row["fit_score"]

    # re-scanning the same source must not alert the same listing again
    calls.clear()
    client.post("/api/radar/scan?source=jobicy", headers=auth_headers(admin))
    assert [c for c in calls if c[1]["id"] == row["id"]] == []


# ---------------------------------------------------------------------------
# Migration idempotency (step 2's 0002_radar_sales_agent)
# ---------------------------------------------------------------------------

def _load_migration_0002():
    path = Path(__file__).parent.parent / "migrations" / "versions" / "0002_radar_sales_agent.py"
    spec = importlib.util.spec_from_file_location("migration_0002_radar_sales_agent", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_migration_0002_adds_columns_only_when_missing(tmp_path):
    """Simulates a database that ran 0001_baseline before these columns
    existed on the model — the one case where upgrade() must actually ALTER
    the table. Then runs it again on the now-upgraded table to confirm the
    inspector-gated skip path is a true no-op, not a 'column exists' error."""
    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext

    db_path = tmp_path / "pre_step2.db"
    engine = sa.create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        conn.execute(sa.text(
            "CREATE TABLE external_listings (id VARCHAR PRIMARY KEY, source VARCHAR, external_id VARCHAR)"
        ))

    mod = _load_migration_0002()

    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            mod.upgrade()
        conn.commit()

    inspector = sa.inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("external_listings")}
    for column in mod.NEW_COLUMNS:
        assert column.name in columns
    indexes = {i["name"] for i in inspector.get_indexes("external_listings")}
    assert "ix_external_listings_fit_score" in indexes
    assert "ix_external_listings_pipeline" in indexes

    # second run against the already-upgraded table — must not raise
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            mod.upgrade()
        conn.commit()

    engine.dispose()


def test_migration_head_from_scratch_is_idempotent(tmp_path, monkeypatch):
    """A brand-new deployment: 0001_baseline's create_all() already includes
    these columns (current models), so 0002 must skip every column/index
    without error — and running 'upgrade head' twice must also be a no-op."""
    from alembic import command
    from alembic.config import Config

    db_path = tmp_path / "fresh.db"
    monkeypatch.setattr("app.config.settings.DATABASE_URL", f"sqlite:///{db_path}")

    backend_root = Path(__file__).parent.parent
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "migrations"))

    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")  # already at head — must be a no-op, not an error

    engine = sa.create_engine(f"sqlite:///{db_path}")
    inspector = sa.inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("external_listings")}
    assert "fit_score" in columns
    assert "pipeline" in columns
    engine.dispose()
