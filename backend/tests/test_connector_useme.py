"""Verifies UsemeConnector against a realistic sample of useme.com's public
jobs RSS feed (structure only — no network call). Not run against the live
feed here: as of 2026-10-10, https://useme.com/pl/rss/jobs/ returns a
Cloudflare JS challenge (HTTP 403) to a plain HTTP client instead of RSS XML,
so useme stays in RADAR_DISABLED_SOURCES (see app/config.py) rather than
risk bypassing that protection to "fix" it.
"""
from app.connectors.useme import UsemeConnector

SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Useme — zlecenia</title>
    <link>https://useme.com/pl/jobs/</link>
    <description>Najnowsze zlecenia na Useme</description>
    <item>
      <title>Potrzebuję strony WWW dla małej firmy</title>
      <link>https://useme.com/pl/jobs/12345/</link>
      <guid>https://useme.com/pl/jobs/12345/</guid>
      <description>&lt;p&gt;Szukam wykonawcy strony typu landing page, budżet do negocjacji.&lt;/p&gt;</description>
      <pubDate>Fri, 10 Oct 2026 08:30:00 +0200</pubDate>
      <category>Strony WWW</category>
      <category>Front-end</category>
    </item>
    <item>
      <title>Grafika na social media</title>
      <link>https://useme.com/pl/jobs/12346/</link>
      <guid>https://useme.com/pl/jobs/12346/</guid>
      <description>&lt;p&gt;5 grafik na Instagram, styl minimalistyczny.&lt;/p&gt;</description>
      <pubDate>Fri, 10 Oct 2026 07:00:00 +0200</pubDate>
      <category>Grafika</category>
    </item>
  </channel>
</rss>
"""


def test_useme_connector_parses_sample_feed(monkeypatch):
    monkeypatch.setattr("app.connectors.useme.get_text", lambda url: SAMPLE_FEED)
    conn = UsemeConnector()

    listings = conn.fetch_listings(limit=50)

    assert len(listings) == 2
    first = listings[0]
    assert first.external_id == "https://useme.com/pl/jobs/12345/"
    assert first.url == "https://useme.com/pl/jobs/12345/"
    assert first.title == "Potrzebuję strony WWW dla małej firmy"
    assert "landing page" in first.description
    assert "<p>" not in first.description
    assert first.category == "Strony WWW"
    assert first.tags == ["Strony WWW", "Front-end"]
    assert first.language == "pl"
    assert first.is_remote is True
    assert first.posted_at is not None


def test_useme_connector_respects_limit(monkeypatch):
    monkeypatch.setattr("app.connectors.useme.get_text", lambda url: SAMPLE_FEED)
    conn = UsemeConnector()

    listings = conn.fetch_listings(limit=1)

    assert len(listings) == 1
