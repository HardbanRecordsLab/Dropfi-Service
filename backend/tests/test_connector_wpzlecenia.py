"""Verifies WpZleceniaConnector against a sample of wpzlecenia.pl's public
WordPress RSS feed (structure only — no network call in the test)."""
from app.connectors.wpzlecenia import WpZleceniaConnector

SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
  <title>WP Zlecenia</title>
  <link>https://wpzlecenia.pl/</link>
  <description>Łączymy wordpressowych specjalistów z ludźmi, którzy potrzebują wordpressowej pomocy</description>
  <item>
    <title>Migracja strony internetowej z Laravel na WordPress</title>
    <link>https://wpzlecenia.pl/2026/08/migracja-strony-internetowej-z-laravel-na-wordpress/</link>
    <dc:creator><![CDATA[admin]]></dc:creator>
    <pubDate>Tue, 11 Aug 2026 18:46:20 +0000</pubDate>
    <category><![CDATA[Zlecenia]]></category>
    <guid isPermaLink="false">https://wpzlecenia.pl/?p=13907</guid>
    <description><![CDATA[<p>Poszukujemy doświadczonego programisty WordPress/PHP do przebudowy istniejącej strony internetowej.</p>]]></description>
  </item>
  <item>
    <title>Postawienie bloga osobistego z wtyczką WooCommerce</title>
    <link>https://wpzlecenia.pl/2026/08/postawienie-bloga-osobistego-z-wtyczka-woocommerce/</link>
    <dc:creator><![CDATA[admin]]></dc:creator>
    <pubDate>Thu, 27 Aug 2026 14:11:37 +0000</pubDate>
    <category><![CDATA[Zlecenia]]></category>
    <guid isPermaLink="false">https://wpzlecenia.pl/?p=13909</guid>
    <description><![CDATA[<p>Zlecę postawienie prostego bloga osobistego z wtyczką WooCommerce.</p>]]></description>
  </item>
</channel>
</rss>
"""


def test_wpzlecenia_connector_parses_sample_feed(monkeypatch):
    monkeypatch.setattr("app.connectors.wpzlecenia.get_text", lambda url: SAMPLE_FEED)
    conn = WpZleceniaConnector()

    listings = conn.fetch_listings(limit=50)

    assert len(listings) == 2
    first = listings[0]
    assert first.external_id == "https://wpzlecenia.pl/?p=13907"
    assert first.url.startswith("https://wpzlecenia.pl/2026/08/")
    assert "Laravel" in first.title
    assert "WordPress/PHP" in first.description
    assert "<p>" not in first.description
    assert first.category == "WordPress"
    assert "wordpress" in first.tags
    assert first.language == "pl"
    assert first.is_remote is True
    assert first.posted_at is not None


def test_wpzlecenia_connector_respects_limit(monkeypatch):
    monkeypatch.setattr("app.connectors.wpzlecenia.get_text", lambda url: SAMPLE_FEED)
    conn = WpZleceniaConnector()

    listings = conn.fetch_listings(limit=1)

    assert len(listings) == 1
