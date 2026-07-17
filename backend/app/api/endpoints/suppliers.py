from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import distinct, extract, func
from sqlalchemy.orm import Session
from backend.app.models.schemas import (
    Invoice,
    LineItem,
    Supplier,
    SupplierStatsResponse,
)
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, RoleChecker
import uuid
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

class SupplierCreate(BaseModel):
    name: str
    taxId: str
    email: Optional[str] = None
    address: Optional[str] = None

class SupplierResponse(BaseModel):
    id: str
    name: str
    taxId: str
    email: Optional[str] = None
    address: Optional[str] = None


def _shift_month(month_start: date, offset: int) -> date:
    month_index = month_start.year * 12 + month_start.month - 1 + offset
    year, month_zero_based = divmod(month_index, 12)
    return date(year, month_zero_based + 1, 1)


def _trailing_year_window(today: date) -> tuple[date, date]:
    current_month = today.replace(day=1)
    return _shift_month(current_month, -11), _shift_month(current_month, 1)


def _monthly_buckets(start: date, end: date) -> list[date]:
    months: list[date] = []
    current = start
    while current < end:
        months.append(current)
        current = _shift_month(current, 1)
    return months


def _as_float(value: Decimal | int | float | None) -> float:
    return float(value or 0)


def _status_distribution(status_totals) -> dict[str, int]:
    distribution = {"Approved": 0, "Rejected": 0, "Pending": 0}
    for status, count in status_totals:
        if status in distribution:
            distribution[status] = count
    return distribution


def _build_monthly_amounts(monthly_totals, start: date, end: date) -> list[dict]:
    monthly_by_key = {
        (int(year), int(month)): _as_float(amount)
        for year, month, amount in monthly_totals
    }
    return [
        {
            "month": month.strftime("%Y-%m"),
            "amount": monthly_by_key.get((month.year, month.month), 0.0),
        }
        for month in _monthly_buckets(start, end)
    ]


@router.get("/{id}/stats", response_model=SupplierStatsResponse)
def get_supplier_stats(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(RoleChecker(["Admin", "Approver"])),
):
    """Return server-aggregated invoice statistics for one supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    start, end = _trailing_year_window(date.today())
    date_filter = (Invoice.date >= start, Invoice.date < end)
    supplier_filter = (Invoice.supplier_id == id, *date_filter)

    total_invoices, total_amount, average_amount = db.query(
        func.count(Invoice.id),
        func.coalesce(func.sum(Invoice.total_amount), 0),
        func.avg(Invoice.total_amount),
    ).filter(*supplier_filter).one()

    grand_total = db.query(
        func.coalesce(func.sum(Invoice.total_amount), 0)
    ).filter(*date_filter).scalar()

    month_year = extract("year", Invoice.date).label("year")
    month_number = extract("month", Invoice.date).label("month")
    monthly_totals = db.query(
        month_year,
        month_number,
        func.coalesce(func.sum(Invoice.total_amount), 0),
    ).filter(*supplier_filter).group_by(month_year, month_number).all()
    monthly_amounts = _build_monthly_amounts(monthly_totals, start, end)

    top_line_items = db.query(
        LineItem.description,
        func.sum(LineItem.total_price).label("total_amount"),
        func.count(distinct(LineItem.invoice_id)).label("invoice_count"),
    ).join(Invoice, LineItem.invoice_id == Invoice.id).filter(
        *supplier_filter,
        LineItem.description.isnot(None),
    ).group_by(
        LineItem.description
    ).order_by(
        func.sum(LineItem.total_price).desc(),
        LineItem.description.asc(),
    ).limit(10).all()

    status_totals = db.query(
        Invoice.status,
        func.count(Invoice.id),
    ).filter(*supplier_filter).group_by(Invoice.status).all()
    status_distribution = _status_distribution(status_totals)

    top_invoice = db.query(Invoice).filter(*supplier_filter).order_by(
        Invoice.total_amount.desc()
    ).first()
    currency_invoice = db.query(Invoice.currency).filter(
        *supplier_filter
    ).order_by(Invoice.date.desc()).first()
    currency = currency_invoice[0] if currency_invoice else "USD"
    grand_total_float = _as_float(grand_total)
    total_amount_float = _as_float(total_amount)

    return SupplierStatsResponse(
        supplierName=supplier.name,
        taxId=supplier.tax_id,
        totalInvoices=total_invoices,
        totalAmount=total_amount_float,
        currency=currency,
        monthlyAmounts=monthly_amounts,
        annualAccumulated=total_amount_float,
        annualPercentage=(total_amount_float / grand_total_float * 100)
        if grand_total_float
        else 0.0,
        grandTotalAllSuppliers=grand_total_float,
        topLineItems=[
            {
                "description": description,
                "totalAmount": _as_float(total),
                "invoiceCount": invoice_count,
            }
            for description, total, invoice_count in top_line_items
        ],
        statusDistribution=status_distribution,
        averageInvoiceAmount=_as_float(average_amount),
        topInvoice=(
            {"number": top_invoice.invoice_number, "amount": _as_float(top_invoice.total_amount)}
            if top_invoice
            else None
        ),
    )

@router.post("", response_model=SupplierResponse)
def create_supplier(
    supplier_in: SupplierCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Creates a new supplier.
    """
    # Check if supplier already exists by tax_id
    existing = db.query(Supplier).filter(Supplier.tax_id == supplier_in.taxId).first()
    if existing:
        raise HTTPException(status_code=400, detail="Supplier with this tax ID already exists")

    new_supplier = Supplier(
        id=uuid.uuid4(),
        name=supplier_in.name,
        tax_id=supplier_in.taxId,
        email=supplier_in.email,
        address=supplier_in.address
    )
    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)
    return SupplierResponse(
        id=str(new_supplier.id),
        name=new_supplier.name,
        taxId=new_supplier.tax_id,
        email=new_supplier.email,
        address=new_supplier.address,
    )

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    taxId: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

@router.put("/{id}", response_model=SupplierResponse)
def update_supplier(
    id: uuid.UUID,
    supplier_in: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Updates an existing supplier's details.
    """
    supplier = db.query(Supplier).filter(Supplier.id == id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    if supplier_in.name is not None:
        supplier.name = supplier_in.name
    if supplier_in.taxId is not None:
        # Check new tax_id doesn't conflict with another supplier
        conflict = db.query(Supplier).filter(
            Supplier.tax_id == supplier_in.taxId,
            Supplier.id != id
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail="Tax ID already in use by another supplier")
        supplier.tax_id = supplier_in.taxId
    if supplier_in.email is not None:
        supplier.email = supplier_in.email
    if supplier_in.address is not None:
        supplier.address = supplier_in.address

    db.commit()
    db.refresh(supplier)
    return SupplierResponse(
        id=str(supplier.id),
        name=supplier.name,
        taxId=supplier.tax_id,
        email=supplier.email,
        address=supplier.address,
    )

@router.get("", response_model=List[SupplierResponse])
def list_suppliers(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Lists all registered suppliers.
    Returns camelCase JSON with taxId instead of tax_id.
    """
    suppliers = db.query(Supplier).all()
    return [
        SupplierResponse(
            id=str(s.id),
            name=s.name,
            taxId=s.tax_id,
            email=s.email,
            address=s.address,
        )
        for s in suppliers
    ]


@router.delete("/{id}")
def delete_supplier(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(RoleChecker(["Admin"])),
):
    """Deletes a supplier. Only allowed if no invoices are associated."""
    supplier = db.query(Supplier).filter(Supplier.id == id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    invoice_count = db.query(Invoice).filter(Invoice.supplier_id == id).count()
    if invoice_count > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot delete supplier: {invoice_count} invoice(s) associated. "
                "Delete the invoices first."
            ),
        )

    db.delete(supplier)
    db.commit()
    return {"status": "success", "deleted_id": str(id)}
