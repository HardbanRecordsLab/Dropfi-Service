from fastapi import APIRouter

from app.utils.currency import rates, tax_hint

router = APIRouter(prefix="/fx", tags=["Currency & Tax"])


@router.get("/rates")
def fx_rates():
    """#F2 Global Currency & Tax Auto-Engine: live PLN-based FX rates (Frankfurter API, 1h cache, static fallback)."""
    return rates()


@router.get("/tax-hint/{country_code}")
def fx_tax_hint(country_code: str):
    """#F2 indicative cross-border VAT/tax note for a buyer country (not legal advice)."""
    return tax_hint(country_code)
