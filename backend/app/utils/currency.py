"""#F2 Global Currency & Tax Auto-Engine.

Self-working FX engine: tries a live provider first, and falls back to a static
snapshot when the network is unavailable. Caches live rates for 1 hour.
"""

from __future__ import annotations

import time
import httpx

# Approximate PLN-based cross rates (snapshot, refresh periodically).
RATES_FROM_PLN = {
    "PLN": 1.0,
    "EUR": 0.23,
    "USD": 0.25,
    "GBP": 0.20,
    "UAH": 10.4,
    "CZK": 5.7,
    "SEK": 2.6,
}

CURRENCY_SYMBOL = {
    "PLN": "zł", "EUR": "€", "USD": "$", "GBP": "£", "UAH": "₴", "CZK": "Kč", "SEK": "kr",
}

# Cache for live rates (refreshed every 3600 seconds)
_cached_rates: dict | None = None
_cached_rates_source: str = "unset"
_cached_rates_time: float = 0.0
_CACHE_TTL = 3600  # 1 hour

# Simplified, non-legal-advice notes shown to clients so cross-border pricing
# isn't a surprise — verified case-by-case via a lawyer for real invoicing.
TAX_NOTES = {
    "PL": {"vat_rate": 0.23, "note": "Domestic PL B2B service: 23% VAT (unless the freelancer is VAT-exempt)."},
    "DE": {"vat_rate": 0.19, "note": "EU cross-border B2B: reverse-charge likely applies (0% VAT invoice, buyer self-assesses)."},
    "US": {"vat_rate": 0.0, "note": "No VAT; check state sales-tax nexus rules for digital services."},
    "GB": {"vat_rate": 0.20, "note": "Post-Brexit: UK reverse-charge may apply for B2B services bought from the EU."},
    "UA": {"vat_rate": 0.20, "note": "Cross-border B2B services are generally VAT-exempt on the Ukrainian buyer side."},
    "DEFAULT": {"vat_rate": 0.0, "note": "Cross-border B2B service — verify local reverse-charge / VAT rules before invoicing."},
}


def _normalize_live_rates(payload: dict) -> dict | None:
    if not isinstance(payload, dict):
        return None
    rates = payload.get("rates")
    if not isinstance(rates, dict):
        return None

    normalized = {"PLN": 1.0}
    for code, value in rates.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if numeric <= 0:
            continue
        normalized[str(code).upper()] = numeric
    return normalized or None


def _fetch_live_rates() -> tuple[dict | None, str]:
    global _cached_rates, _cached_rates_source, _cached_rates_time

    # Return cached rates if still valid
    if _cached_rates is not None and (time.time() - _cached_rates_time) < _CACHE_TTL:
        return _cached_rates, _cached_rates_source

    try:
        response = httpx.get("https://api.frankfurter.app/latest?from=PLN", timeout=5.0)
        response.raise_for_status()
        normalized = _normalize_live_rates(response.json())
        if normalized:
            _cached_rates = normalized
            _cached_rates_source = "live"
            _cached_rates_time = time.time()
            return normalized, "live"
    except Exception:
        pass
    return RATES_FROM_PLN, "fallback"


def convert(amount_pln: float, target: str) -> float:
    rates, _ = _fetch_live_rates()
    rate = rates.get((target or "PLN").upper(), 1.0)
    return round(amount_pln * rate, 2)


def rates() -> dict:
    live_rates, source = _fetch_live_rates()
    return {"base": "PLN", "rates": live_rates, "symbols": CURRENCY_SYMBOL, "source": source}


def tax_hint(country_code: str) -> dict:
    return TAX_NOTES.get((country_code or "").upper(), TAX_NOTES["DEFAULT"])
