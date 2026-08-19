"""#F2 Global Currency & Tax Auto-Engine.

Static FX snapshot + indicative cross-border VAT/tax hints — zero external
dependency by default (self-working, like every other AI feature's fallback),
swappable later for a live FX provider by editing RATES_FROM_PLN.
"""

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


def convert(amount_pln: float, target: str) -> float:
    rate = RATES_FROM_PLN.get((target or "PLN").upper(), 1.0)
    return round(amount_pln * rate, 2)


def rates() -> dict:
    return {"base": "PLN", "rates": RATES_FROM_PLN, "symbols": CURRENCY_SYMBOL}


def tax_hint(country_code: str) -> dict:
    return TAX_NOTES.get((country_code or "").upper(), TAX_NOTES["DEFAULT"])
