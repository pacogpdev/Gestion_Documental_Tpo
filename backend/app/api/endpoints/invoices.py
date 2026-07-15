from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from backend.app.models.schemas import Invoice, LineItem, Supplier, InvoiceResponse
from backend.app.services.ai_service import extract_invoice_data
from backend.app.core.security import get_current_user, RoleChecker
from backend.app.core.database import get_db
import uuid
from datetime import datetime, date

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _resolve_supplier(db: Session, extraction_result: dict) -> tuple:
    """
    Resolve or create a supplier from extraction data.
    Edge case #4: when no tax_id is extracted, use supplier_name as a
    pseudo-tax_id so different unnamed suppliers don't collide.
    Returns (supplier, supplier_name).
    """
    raw_tax_id = extraction_result.get("tax_id")
    supplier_name = (extraction_result.get("supplier_name") or "Unknown Supplier").strip()

    if raw_tax_id:
        tax_id = raw_tax_id.strip()
    elif supplier_name and supplier_name != "Unknown Supplier":
        # Use the name as a pseudo-tax_id so same unnamed supplier maps to same record
        tax_id = f"unnamed:{supplier_name.upper()}"
    else:
        # Completely unknown supplier — give it a unique id so each upload is separate
        tax_id = f"unnamed:{uuid.uuid4().hex[:8].upper()}"

    supplier = db.query(Supplier).filter(Supplier.tax_id == tax_id).first()
    if not supplier:
        supplier = Supplier(
            id=uuid.uuid4(),
            name=supplier_name or "Unknown Supplier",
            tax_id=tax_id
        )
        db.add(supplier)
        db.flush()
    elif supplier.name != supplier_name and supplier_name:
        supplier.name = supplier_name
        db.flush()

    return supplier, supplier_name


def _normalize_invoice_number(raw: str | None) -> str:
    """
    Normalize invoice number: trim whitespace (edge case #5) and uppercase
    (edge case #1) so 'fac-001 ' and 'FAC-001' match the same record.
    """
    normalized = (raw or "").strip().upper()
    if not normalized:
        normalized = f"MANUAL-{uuid.uuid4().hex[:8].upper()}"
    return normalized


@router.post("/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(RoleChecker(["Clerk", "Admin"]))
):
    """
    Uploads an invoice, extracts data using AI, and PERSISTS it to the database.
    """
    # 1. Extract data using the AI service
    content = await file.read()
    extraction_result = await extract_invoice_data(content, filename=file.filename or "invoice.pdf")

    # 2. Handle Supplier
    supplier, supplier_name = _resolve_supplier(db, extraction_result)

    # 3. Normalize invoice number (trim + uppercase)
    invoice_number = _normalize_invoice_number(extraction_result.get("invoice_number"))

    # 4. Check for duplicate invoice number for the same supplier
    existing = db.query(Invoice).filter(
        Invoice.invoice_number == invoice_number,
        Invoice.supplier_id == supplier.id
    ).first()

    if existing:
        # Edge case #2: if the existing invoice was Rejected, replace it
        if existing.status == "Rejected":
            db.query(LineItem).filter(LineItem.invoice_id == existing.id).delete()
            db.delete(existing)
            db.flush()
        else:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate invoice: invoice number '{invoice_number}' already exists for supplier '{supplier_name}'."
            )

    invoice_date = extraction_result.get("date") or date.today()
    new_invoice = Invoice(
        id=uuid.uuid4(),
        supplier_id=supplier.id,
        invoice_number=invoice_number,
        date=invoice_date,
        total_amount=extraction_result.get("total_amount", 0.0),
        currency=extraction_result.get("currency", "EUR"),
        status="Pending",
        file_url=f"/uploads/{file.filename}"
    )
    db.add(new_invoice)
    db.flush()

    # 5. Create Line Items
    for item in extraction_result["line_items"]:
        li = LineItem(
            id=uuid.uuid4(),
            invoice_id=new_invoice.id,
            description=item["description"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            total_price=item["total_price"]
        )
        db.add(li)

    # 6. COMMIT everything to DB
    # Edge case #3: catch DB-level IntegrityError as race-condition safety net
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate invoice: invoice number '{invoice_number}' already exists for supplier '{supplier_name}' (race condition caught)."
        )
    db.refresh(new_invoice)
    
    return {
        "status": "success",
        "invoice_id": new_invoice.id,
        "extracted_data": extraction_result
    }

@router.get("", response_model=list[InvoiceResponse])
def list_invoices(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Lists all invoices for the approval dashboard.
    Returns camelCase JSON with supplier name resolved.
    """
    invoices = db.query(Invoice).options(selectinload(Invoice.supplier)).all()
    return [
        InvoiceResponse(
            id=str(inv.id),
            invoiceNumber=inv.invoice_number,
            supplierName=inv.supplier.name,
            date=inv.date,
            totalAmount=float(inv.total_amount),
            currency=inv.currency,
            status=inv.status,
        )
        for inv in invoices
    ]

from pydantic import BaseModel

class StatusUpdate(BaseModel):
    status: str

@router.delete("/{id}")
def delete_invoice(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(RoleChecker(["Clerk", "Admin"]))
):
    """
    Deletes an invoice and its line items.
    """
    invoice = db.query(Invoice).filter(Invoice.id == id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Delete associated line items first (FK constraint)
    db.query(LineItem).filter(LineItem.invoice_id == id).delete()
    db.delete(invoice)
    db.commit()
    
    return {"status": "success", "deleted_id": str(id)}

@router.patch("/{id}/approve")
async def update_invoice_status(
    id: uuid.UUID,
    body: StatusUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(RoleChecker(["Approver", "Admin"]))
):
    """
    Updates invoice status. Matches FE call /invoices/{id}/approve.
    """
    invoice = db.query(Invoice).filter(Invoice.id == id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice.status = body.status
    db.commit()
    
    return {"status": "success", "new_status": body.status}
