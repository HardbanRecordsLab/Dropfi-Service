"""Radar → marketplace import: currency conversion, top-up to a minimum of open
jobs, quiet matching for leads, expiry of stale imports."""
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models import ExternalListing, Job, Notification
from app.utils import radar_import
from tests.helpers import make_freelancer


def _row(**kw):
    base = dict(source="freelancer", external_id=kw.pop("external_id"), url="https://example.test/p/1",
                title="Lead", description="A sufficiently long description of the project for import " * 2,
                status="new", posted_at=datetime.now(timezone.utc), fit_score=40.0)
    base.update(kw)
    return ExternalListing(**base)


def test_budget_to_pln_converts_from_text_and_currency(monkeypatch):
    monkeypatch.setattr(radar_import, "_fetch_live_rates", lambda: ({"PLN": 1.0, "USD": 0.25, "INR": 23.0}, "test"))
    assert radar_import.budget_to_pln(_row(external_id="a", budget_text="$30 - $250", currency="USD")) == (1000.0, True)
    assert radar_import.budget_to_pln(_row(external_id="b", budget_text="₹1500 - ₹12500", currency="INR"))[0] == 543.0
    assert radar_import.budget_to_pln(_row(external_id="c", budget_text="$2 - $5", currency="USD")) == (50.0, True)
    assert radar_import.budget_to_pln(_row(external_id="d", budget_max=3000.0, currency="PLN")) == (3000.0, True)
    assert radar_import.budget_to_pln(_row(external_id="e", budget_text="", currency="")) == (500.0, False)


def test_top_up_reaches_target_quietly_and_expires_stale(client, monkeypatch):
    monkeypatch.setattr(radar_import, "_fetch_live_rates", lambda: ({"PLN": 1.0, "USD": 0.25}, "test"))
    fr = make_freelancer(client, bio="Moonlight glassblowing artisan, decorative lanterns", skills=["glassblowing"])
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        rows = [
            _row(external_id=f"topup-{i}", title=f"Glassblowing lantern commission {i}",
                 description="Hand blown decorative glass lanterns, glassblowing artisan wanted. " * 2,
                 budget_text="$100 - $200", currency="USD")
            for i in range(6)
        ]
        rows.append(_row(external_id="topup-old", title="Old glass gig", posted_at=now - timedelta(days=60)))
        rows.append(_row(external_id="topup-short", title="Short glass gig", description="too short"))
        rows.append(_row(external_id="topup-dupe", title="Glassblowing lantern commission 0",
                         description="Cross-posted duplicate of an earlier lead, glassblowing lanterns. " * 2, fit_score=10.0))
        db.add_all(rows)
        db.commit()

        target = radar_import.open_jobs_count(db) + 4
        result = radar_import.top_up_open_jobs(db, target=target)
        assert result["imported"] == 4 and result["open_after"] >= target
        # already at target -> nothing more
        assert radar_import.top_up_open_jobs(db, target=target)["imported"] == 0

        imported = db.query(Job).filter(Job.external_source == "freelancer", Job.title.like("Glassblowing lantern%")).all()
        assert len(imported) == 4, imported
        assert all(j.budget == 800.0 for j in imported), [(j.budget, j.description[-200:]) for j in imported]
        assert all("≈ 800 PLN" in j.description for j in imported)
        assert db.query(ExternalListing).filter_by(external_id="topup-old").one().status == "new"
        assert db.query(ExternalListing).filter_by(external_id="topup-short").one().status == "new"
        assert db.query(ExternalListing).filter_by(external_id="topup-dupe").one().status == "new"

        # freelancer was matched in-app but never e-mailed (no autopilot contract either)
        notes = db.query(Notification).filter(Notification.user_id == fr["user"]["id"]).count()
        assert notes >= 1

        # stale imports close
        for j in imported[:2]:
            j.created_at = now - timedelta(days=30)
        db.commit()
        assert radar_import.expire_stale_imports(db, max_age_days=14) >= 2
    finally:
        db.close()


def test_budget_junk_range_uses_realistic_point(monkeypatch):
    monkeypatch.setattr(radar_import, "_fetch_live_rates", lambda: ({"PLN": 1.0, "USD": 0.25}, "test"))
    assert radar_import.budget_to_pln(_row(external_id="j", budget_text="$10 - $100000", currency="USD")) == (120.0, True)


def test_llm_analysis_prompt_formats_and_parses(monkeypatch):
    """Regression: literal JSON braces in ANALYSIS_PROMPT made .format() raise
    KeyError on every LLM call, so production matching never ran with a key set."""
    from app.utils import ai
    seen = {}

    def fake_llm(prompt, **kw):
        seen["prompt"] = prompt
        return ('{"category": "Web Development", "subcategory": "x", "skills": ["php"], "urgency": "low",'
                ' "experience_level": "mid", "fair_price": 900, "key_requirements": "y"}')

    monkeypatch.setattr(ai, "llm_enabled", lambda: True)
    monkeypatch.setattr(ai, "llm_text", fake_llm)
    out = ai.analyze_job("Shop build", "Build a WooCommerce shop", 1000, "2026-12-01", "Remote")
    assert out["model"] == "llm" and out["fair_price"] == 900
    assert '"category": one of' in seen["prompt"] and "Shop build" in seen["prompt"]
