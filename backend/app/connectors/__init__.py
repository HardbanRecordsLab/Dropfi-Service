"""Portal Radar connectors.

Each connector pulls job leads (demand side) and/or contractor profiles
(supply side) from ONE external portal, using that portal's **official API,
RSS feed or public data endpoint only** — never HTML scraping that a site's
Terms of Service forbid. A connector that needs an API key self-disables
(``is_enabled() -> False``) until the key is set in the environment.

Add a connector by subclassing ``Connector`` (see ``base.py``) and appending
an instance to ``ALL_CONNECTORS`` in ``registry.py``.
"""
