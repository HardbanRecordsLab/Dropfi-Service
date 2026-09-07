"""#5 Invoicing: generate platform fee invoices for B2B accounting.

Creates Invoice records from completed Payment rows, calculates VAT,
and provides invoice numbering (sequential, per-year).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Invoice, Payment, Contract, User


def _next_invoice_number(db: Session) -> str:
    """Generate next sequential invoice number: DROPIFY-2026-0001."""
    year = datetime.now(timezone.utc).year
    prefix = f"{settings.INVOICE_PREFIX}-{year}-"
    last = (
        db.query(Invoice)
        .filter(Invoice.invoice_number.like(f"{prefix}%"))
        .order_by(Invoice.invoice_number.desc())
        .first()
    )
    if last:
        try:
            seq = int(last.invoice_number.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def _determine_vat_rate(buyer_country: str | None) -> float:
    """Determine VAT rate based on buyer location.

    - PL domestic: 23%
    - EU cross-border B2B: 0% (reverse-charge)
    - Non-EU: 0%
    """
    if (buyer_country or "").upper() == "PL":
        return settings.INVOICE_VAT_RATE
    return 0.0  # reverse-charge or non-EU


def generate_invoice(
    db: Session,
    contract_id: str,
    payer_id: str | None = None,
) -> Invoice | None:
    """Generate an invoice for platform fees on a completed contract.

    Collects all 'paid' payments for the contract and creates a single
    invoice covering the platform_fee总额. Returns None if no eligible payments.
    """
    contract = db.get(Contract, contract_id)
    if not contract:
        return None

    # Find paid payments not yet invoiced
    payments = (
        db.query(Payment)
        .filter(
            Payment.contract_id == contract_id,
            Payment.status.in_(["paid", "paid_out"]),
        )
        .all()
    )
    if not payments:
        return None

    # Filter out already-invoiced payments
    already_invoiced = set()
    existing = db.query(Invoice.payment_ids).filter(Invoice.contract_id == contract_id).all()
    for (ids,) in existing:
        if ids:
            already_invoiced.update(ids)
    new_payments = [p for p in payments if p.id not in already_invoiced]
    if not new_payments:
        return None

    # Calculate totals
    subtotal = round(sum(p.platform_fee for p in new_payments), 2)
    if subtotal <= 0:
        return None

    # Determine buyer info
    payer = db.get(User, payer_id or contract.client_id)
    buyer_name = f"{payer.first_name} {payer.last_name}".strip() if payer else "Unknown"
    if payer and payer.company:
        buyer_name = payer.company
    buyer_country = payer.country if payer else None

    vat_rate = _determine_vat_rate(buyer_country)
    vat_amount = round(subtotal * vat_rate, 2)
    total = round(subtotal + vat_amount, 2)

    invoice = Invoice(
        invoice_number=_next_invoice_number(db),
        contract_id=contract_id,
        payer_id=payer.id if payer else contract.client_id,
        seller_name=settings.PLATFORM_NAME,
        seller_address=settings.PLATFORM_ADDRESS,
        seller_nip=settings.PLATFORM_NIP or None,
        buyer_name=buyer_name,
        buyer_address=payer.location if payer else None,
        buyer_nip=getattr(payer, "nip", None),
        buyer_country=buyer_country,
        subtotal=subtotal,
        vat_rate=vat_rate,
        vat_amount=vat_amount,
        total=total,
        currency=settings.INVOICE_CURRENCY,
        status="issued",
        issued_at=datetime.now(timezone.utc),
        due_date=datetime.now(timezone.utc) + timedelta(days=settings.INVOICE_PAYMENT_DAYS),
        payment_ids=[p.id for p in new_payments],
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def get_invoice_summary(db: Session) -> dict:
    """Revenue summary with VAT breakdown for admin dashboard."""
    from sqlalchemy import func

    total_subtotal = db.query(func.coalesce(func.sum(Invoice.subtotal), 0)).scalar()
    total_vat = db.query(func.coalesce(func.sum(Invoice.vat_amount), 0)).scalar()
    total_total = db.query(func.coalesce(func.sum(Invoice.total), 0)).scalar()
    issued_count = db.query(Invoice).filter(Invoice.status == "issued").count()
    paid_count = db.query(Invoice).filter(Invoice.status == "paid").count()

    return {
        "subtotal": round(float(total_subtotal), 2),
        "vat": round(float(total_vat), 2),
        "total": round(float(total_total), 2),
        "currency": settings.INVOICE_CURRENCY,
        "issued": issued_count,
        "paid": paid_count,
    }
