"""Verifies FreelancerConnector against a realistic sample of the official
freelancer.com/api/projects/0.1/projects/active response (structure only —
no network call in the test, no real token needed)."""
from app.connectors.freelancer import FreelancerConnector

SAMPLE_RESPONSE = {
    "status": "success",
    "result": {
        "projects": [
            {
                "id": 40761277,
                "title": "Harden WordPress Firewall & Server",
                "seo_url": "firewall/Harden-WordPress-Firewall-Server",
                "currency": {"id": 1, "code": "USD", "sign": "$"},
                "description": "My WordPress site is currently offline after malicious files were discovered.",
                "jobs": [
                    {"id": 3, "name": "PHP"},
                    {"id": 69, "name": "WordPress"},
                    {"id": 33, "name": "Web Security"},
                ],
                "budget": {"minimum": 30.0, "maximum": 250.0},
                "language": "en",
                "time_submitted": 1791669695,
            },
            {
                "id": 40761251,
                "title": "Eficiencia Responsive WordPress y Elementor Pro",
                "seo_url": "wordpress/Eficiencia-Responsive-WordPress",
                "currency": {"id": 1, "code": "USD", "sign": "$"},
                "description": "Correcciones responsive en WordPress y Elementor Pro.",
                "jobs": [{"id": 69, "name": "WordPress"}],
                "budget": {"minimum": 2.0, "maximum": 8.0},
                "language": "es",
                "time_submitted": 1791669000,
            },
        ],
    },
}


def test_freelancer_connector_parses_sample_response(monkeypatch):
    monkeypatch.setattr("app.connectors.freelancer.get_json", lambda url, params=None, headers=None: SAMPLE_RESPONSE)
    conn = FreelancerConnector()

    listings = conn.fetch_listings(limit=10)

    assert len(listings) == 2
    first = listings[0]
    assert first.external_id == "40761277"
    assert first.url == "https://www.freelancer.com/projects/firewall/Harden-WordPress-Firewall-Server"
    assert first.title == "Harden WordPress Firewall & Server"
    assert first.category == "PHP"
    assert "WordPress" in first.tags
    assert first.budget_text == "$30 - $250"
    # the amounts keep their own currency (USD here) and are converted to USD where they are compared, so a USD figure
    # is never misread as PLN — and leads below the agency minimum can be filtered
    assert first.budget_min == 30.0 and first.budget_max == 250.0 and first.currency == "USD"
    assert first.language == "en"
    assert first.is_remote is True
    assert first.posted_at is not None

    assert listings[1].language == "es"


def test_freelancer_connector_respects_limit(monkeypatch):
    monkeypatch.setattr("app.connectors.freelancer.get_json", lambda url, params=None, headers=None: SAMPLE_RESPONSE)
    conn = FreelancerConnector()

    listings = conn.fetch_listings(limit=1)

    assert len(listings) == 1


def test_freelancer_connector_disabled_without_token(monkeypatch):
    monkeypatch.setattr("app.config.settings.FREELANCER_ACCESS_TOKEN", "")
    conn = FreelancerConnector()
    assert conn.is_enabled() is False
