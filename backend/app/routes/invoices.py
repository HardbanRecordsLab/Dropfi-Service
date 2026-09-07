"""#5 Invoicing routes: generate, list, and retrieve platform fee invoices."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import User, Invoice
from app.schemas import ORMModel
from app.utils.invoicing import generate_invoice, get_invoice_summary


router = APIRouter(prefix="/invoices", tags=["Invoices"])


class InvoiceOut(ORMModel):
    id: str
    invoice_number: str
    contract_id: str
    payer_id: str
    seller_name: str
    seller_nip: str | None
    buyer_name: str
    buyer_nip: str | None
    buyer_country: str | None
    subtotal: float
    vat_rate: float
    vat_amount: float
    total: float
    currency: str
    status: str
    issued_at: str | None
    due_date: str | None
    paid_at: str | None
    payment_ids: list[str]


class InvoiceSummaryOut(ORMModel):
    subtotal: float
    vat: float
    total: float
    currency: str
    issued: int
    paid: int


@router.post("/generate/{contract_id}", response_model=InvoiceOut)
def generate_contract_invoice(
    contract_id: str,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Admin-only: generate invoice for platform fees on a completed contract."""
    invoice = generate_invoice(db, contract_id)
    if not invoice:
        raise HTTPException(status_code=400, detail="No eligible payments for invoicing")
    return invoice


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List invoices — admins see all, clients see their own."""
    q = db.query(Invoice)
    if user.role != "admin":
        q = q.filter(Invoice.payer_id == user.id)
    return q.order_by(Invoice.issued_at.desc()).all()


@router.get("/summary", response_model=InvoiceSummaryOut)
def invoice_summary(
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Admin-only: revenue summary with VAT breakdown."""
    return get_invoice_summary(db)


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if user.role != "admin" and invoice.payer_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return invoice
