"""Verifies FreelancehuntConnector against a realistic sample of the official
api.freelancehunt.com/v2 JSON:API response (structure only — no network call
in the test, no real token needed)."""
from app.connectors.freelancehunt import FreelancehuntConnector

SAMPLE_RESPONSE = {
    "data": [
        {
            "id": 1658186,
            "type": "project",
            "attributes": {
                "name": "Перенос сайта на вордпрес",
                "description": "Хотим перенести сайт на вордпресс и полностью сохранить дизайн.",
                "skills": [
                    {"id": 78, "name": "Content Management Systems"},
                    {"id": 96, "name": "Website Development"},
                ],
                "status": {"id": 11, "name": "Open for proposals"},
                "budget": {"amount": 4000, "currency": "UAH"},
                "bid_count": 79,
                "is_remote_job": False,
                "location": None,
                "employer": {"id": 578667, "login": "deRed1", "first_name": "Andrii", "last_name": "Ryzhenko"},
                "tags": [{"id": 1, "name": "wordpress"}, {"id": 2, "name": "tilda"}],
                "published_at": "2026-10-10T21:40:00+03:00",
                "expired_at": "2026-10-24T21:40:00+03:00",
            },
            "links": {
                "self": {
                    "api": "https://api.freelancehunt.com/v2/projects/1658186",
                    "web": "https://freelancehunt.com/project/perenos-sajta-na-vordpres/1658186.html",
                },
            },
        },
        {
            "id": 1658215,
            "type": "project",
            "attributes": {
                "name": "Need a landing page built in WordPress",
                "description": "Looking for a developer to build a simple landing page in WordPress with a contact form.",
                "skills": [{"id": 43, "name": "Web Design"}],
                "status": {"id": 11, "name": "Open for proposals"},
                "budget": None,
                "bid_count": 3,
                "is_remote_job": True,
                "location": None,
                "employer": {"id": 999, "login": "janedoe", "first_name": "Jane", "last_name": "Doe"},
                "tags": [],
                "published_at": "2026-10-10T20:00:00+03:00",
                "expired_at": None,
            },
            "links": {
                "self": {
                    "api": "https://api.freelancehunt.com/v2/projects/1658215",
                    "web": "https://freelancehunt.com/project/landing-page-wordpress/1658215.html",
                },
            },
        },
    ],
}


def _mock_get_json(url, params=None, headers=None):
    # Only page 1 has data — mirrors a real paginated API and lets the
    # connector's "stop on empty page" logic terminate the loop correctly.
    if (params or {}).get("page[number]") == 1:
        return SAMPLE_RESPONSE
    return {"data": []}


def test_freelancehunt_connector_parses_sample_response(monkeypatch):
    monkeypatch.setattr("app.connectors.freelancehunt.get_json", _mock_get_json)
    conn = FreelancehuntConnector()

    listings = conn.fetch_listings(limit=10)

    assert len(listings) == 2
    ru, en = listings

    assert ru.external_id == "1658186"
    assert ru.url == "https://freelancehunt.com/project/perenos-sajta-na-vordpres/1658186.html"
    assert ru.company == "Andrii Ryzhenko"
    assert ru.category == "Content Management Systems"
    assert "wordpress" in ru.tags
    assert ru.budget_text == "4000 UAH"
    # UAH must never be passed through as a PLN figure to the scorer
    assert ru.budget_min == 4000 and ru.budget_max == 4000 and ru.currency == "UAH"   # kept in its own currency, converted where compared
    assert ru.language == "uk"
    assert ru.is_remote is True
    assert ru.posted_at is not None

    assert en.external_id == "1658215"
    assert en.budget_text == ""
    assert en.budget_min is None
    assert en.language == "en"
    assert "WordPress" in en.title


def test_freelancehunt_connector_respects_limit(monkeypatch):
    monkeypatch.setattr("app.connectors.freelancehunt.get_json", _mock_get_json)
    conn = FreelancehuntConnector()

    listings = conn.fetch_listings(limit=1)

    assert len(listings) == 1


def test_freelancehunt_connector_disabled_without_token(monkeypatch):
    monkeypatch.setattr("app.config.settings.FREELANCEHUNT_API_TOKEN", "")
    conn = FreelancehuntConnector()
    assert conn.is_enabled() is False
