from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.models.schemas import Supplier
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
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
