"""Portal Radar: budget gate, repost detection, and the portal status/bid-count refresh (no network)."""
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models import ExternalListing
from app.tasks import radar as radar_tasks
from app.utils import radar_market
from app.utils.radar_market import find_duplicate_ids, market_adjustment, similar_titles
from app.utils.radar_scoring import BELOW_MIN_BUDGET_CAP, score_listing

PROFILE = {
    "tagline": "Websites and web apps for businesses",
    "services": [{"name": "Website", "description": "company sites, landing pages, CMS"}],
    "keywords_include": ["website", "landing page"],
    "keywords_exclude": [],
    "languages": ["en"],
    "min_budget_usd": 249,
}


class _Listing:
    def __init__(self, **kw):
        self.title = kw.get("title", "Website for a roofing company")
        self.description = kw.get("description", "We need a landing page website, mobile friendly")
        self.category = ""
        self.tags = []
        self.budget_min = kw.get("budget_min")
        self.budget_max = kw.get("budget_max")
        self.budget_text = ""
        self.currency = kw.get("currency")
        self.language = "en"
        self.posted_at = None


# ---- scoring gate ---------------------------------------------------------------------------------------------------

def test_budget_below_agency_minimum_is_capped_below_alert_threshold(monkeypatch):
    from app.utils import currency
    monkeypatch.setattr(currency, "_fetch_live_rates", lambda: (currency.RATES_FROM_USD, "fallback"))   # no network, no cache from other tests
    tiny_inr = _Listing(budget_min=1500, budget_max=12500, currency="INR")     # about $142
    ok_usd = _Listing(budget_min=250, budget_max=750, currency="USD")
    tiny_score, reason = score_listing(tiny_inr, PROFILE)
    ok_score, _ = score_listing(ok_usd, PROFILE)
    assert tiny_score <= BELOW_MIN_BUDGET_CAP < 30
    assert "poniżej minimum" in reason
    assert ok_score > BELOW_MIN_BUDGET_CAP


def test_unknown_budget_is_not_capped():
    score, reason = score_listing(_Listing(), PROFILE)
    assert "poniżej minimum" not in reason


def test_excluded_service_only_in_description_lowers_the_score_but_in_title_zeroes_it():
    profile = {**PROFILE, "keywords_exclude": ["copywriting"]}
    side_remark = _Listing(description="Company website with landing page. Copywriting is provided by me.")
    in_title = _Listing(title="Copywriting for a website", description="Landing page text")
    clean = _Listing(description="Company website with landing page.")
    side_score, side_reason = score_listing(side_remark, profile)
    clean_score, _ = score_listing(clean, profile)
    title_score, title_reason = score_listing(in_title, profile)
    assert 0 < side_score < clean_score and "spoza oferty" in side_reason
    assert title_score == 0 and "Wykluczone" in title_reason


# ---- reposts --------------------------------------------------------------------------------------------------------

def test_same_job_posted_with_different_titles_is_a_repost():
    a = "PRESTIA AI SaaS Platform Full-Stack Developer"
    b = "Full-Stack Development for PRESTIA AI Platform"
    c = "Prestia AI Platform: Next.js Full-Stack Developer"
    assert similar_titles(a, b) and similar_titles(a, c)


def test_different_jobs_are_not_reposts():
    assert not similar_titles("Wordpress website for selling used forklifts", "Mobile-Friendly Site for Roofing Company")
    assert not similar_titles("Logo", "Logo")        # fewer than two significant words: too little to call it a repost


def test_find_duplicates_keeps_the_best_lead_of_each_group():
    leads = [("a", "PRESTIA AI SaaS Platform Full-Stack Developer", 53.0),
             ("b", "Full-Stack Development for PRESTIA AI Platform", 52.0),
             ("c", "Prestia AI Platform: Next.js Full-Stack Developer", 52.0),
             ("d", "Shopify social media integration", 54.0)]
    assert find_duplicate_ids(leads) == {"b": "a", "c": "a"}


# ---- market signals -------------------------------------------------------------------------------------------------

def test_market_adjustment():
    assert market_adjustment(None) == (0, None, False)
    delta, note, closed = market_adjustment({"open": False, "status": "frozen", "bids": 159})
    assert closed and "frozen" in note
    assert market_adjustment({"open": True, "bids": 40}) == (0, None, False)
    assert market_adjustment({"open": True, "bids": 124})[0] == -radar_market.CROWDED_PENALTY
    assert market_adjustment({"open": True, "bids": 256})[0] == -radar_market.VERY_CROWDED_PENALTY


def test_status_open_rules():
    assert radar_market._status_is_open("freelancer", "active")
    assert not radar_market._status_is_open("freelancer", "frozen")
    assert not radar_market._status_is_open("freelancehunt", "Contractor chosen")
    assert not radar_market._status_is_open("freelancehunt", "Suspended by administration")
    assert radar_market._status_is_open("freelancehunt", "Open for proposals")


# ---- refresh task (DB) ----------------------------------------------------------------------------------------------

def _lead(db, ext_id, title, fit):
    row = ExternalListing(source="freelancer", external_id=ext_id, url=f"https://example.com/{ext_id}", title=title,
                          description="x", status="new", fit_score=fit, fit_reason="ok", fetched_at=datetime.now(timezone.utc))
    db.add(row)
    db.commit()
    return row.id


def test_refresh_closes_dismisses_and_penalizes_and_is_idempotent(client, monkeypatch):
    db = SessionLocal()
    try:
        closed_id = _lead(db, "mkt-closed", "Unique widget zebra platform build", 55)
        crowded_id = _lead(db, "mkt-crowded", "Quantum llama dashboard integration", 54)
        fine_id = _lead(db, "mkt-fine", "Orchid harbour booking portal redesign", 50)
        calls = {"n": 0}
        ours = {"mkt-closed", "mkt-crowded", "mkt-fine"}

        def fake_fetch(source, external_id):
            if external_id in ours:
                calls["n"] += 1          # leads left over from other tests are not our concern
            return {"mkt-closed": {"open": False, "status": "frozen", "bids": 10},
                    "mkt-crowded": {"open": True, "status": "active", "bids": 130},
                    "mkt-fine": {"open": True, "status": "active", "bids": 12}}.get(external_id)

        monkeypatch.setattr(radar_market, "fetch_market", fake_fetch)
        result = radar_tasks.refresh_lead_market()
        assert result["closed"] >= 1 and result["crowded"] >= 1

        db.expire_all()
        closed, crowded, fine = (db.get(ExternalListing, i) for i in (closed_id, crowded_id, fine_id))
        assert closed.fit_score == 0 and closed.status == "dismissed" and "frozen" in closed.fit_reason
        assert crowded.fit_score == 54 - radar_market.CROWDED_PENALTY and crowded.status == "new"
        assert fine.fit_score == 50

        # running again within the recheck window neither re-calls the portal nor stacks the penalty
        before = calls["n"]
        radar_tasks.refresh_lead_market()
        db.expire_all()
        assert calls["n"] == before
        assert db.get(ExternalListing, crowded_id).fit_score == 54 - radar_market.CROWDED_PENALTY
    finally:
        db.close()
