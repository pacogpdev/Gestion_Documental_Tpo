---
name: invoices-api
description: >
  FastAPI endpoint patterns for invoices, suppliers, and users. Pydantic validation, dependency injection, status codes, UUID routing.
  Trigger: When editing files in backend/app/api/, adding or modifying FastAPI endpoints, request/response handling.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Creating or editing FastAPI route handlers in `backend/app/api/endpoints/`
- Adding Pydantic validation to request bodies or response models
- Working with HTTP status codes, dependency injection, or error responses

## Critical Patterns

### Router structure

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, RoleChecker

router = APIRouter(prefix="/invoices", tags=["invoices"])
```

### Endpoint patterns

| Method | Pattern | Use |
|--------|---------|-----|
| POST | `@router.post("/upload")` | File upload + creation |
| GET | `@router.get("")` | List resources |
| PATCH | `@router.patch("/{id}/approve")` | Status update |
| DELETE | `@router.delete("/{id}")` | Resource deletion |

### Request validation with Pydantic

Inline models for simple requests:

```python
from pydantic import BaseModel

class StatusUpdate(BaseModel):
    status: str
```

Use `Depends()` for shared dependencies — never repeat validation logic across endpoints.

### Status code convention

| Code | When |
|------|------|
| 200 | Successful read, update, delete |
| 201 | Successful creation (POST upload) |
| 400 | Invalid input |
| 404 | Resource not found |
| 409 | Duplicate resource (invoice_number + supplier_id conflict) |
| 422 | Validation error |
| 403 | Insufficient permissions (RoleChecker) |
| 401 | Unauthenticated / Invalid token |

### Response model convention

Use camelCase Pydantic response models with `from_attributes = True`:

```python
class InvoiceResponse(BaseModel):
    id: str
    invoiceNumber: str
    supplierName: str
    date: date
    totalAmount: float
    currency: str
    status: str

    class Config:
        from_attributes = True
```

Return at the router level: `@router.get("", response_model=list[InvoiceResponse])`

### UUID routing

```python
import uuid

@router.delete("/{id}")
def delete_invoice(id: uuid.UUID, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    # ...
```

FastAPI auto-validates UUID format from the path param. No manual parsing needed.

### Role-based access

```python
@router.post("/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _ = Depends(RoleChecker(["Clerk", "Admin"]))
):
```

- `get_current_user` — validates JWT (or returns dev user in local mode)
- `RoleChecker(["Clerk", "Admin"])` — enforces role authorization
- Underscore `_` signals the dependency is only used for its side effect

### Error response pattern

Always return a descriptive `detail` string:

```python
raise HTTPException(
    status_code=409,
    detail=f"Duplicate invoice: invoice number '{invoice_number}' already exists for supplier '{supplier_name}'."
)
```

### Dependency injection order

```python
async def endpoint(
    file: UploadFile = File(...),   # 1. Path/query/body params first
    db: Session = Depends(get_db),  # 2. Service dependencies
    current_user = Depends(get_current_user),  # 3. Auth
    _ = Depends(RoleChecker(...))   # 4. Authorization (side-effect only)
):
```

### File upload handling

```python
@router.post("/upload")
async def upload_invoice(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    # process content...
```

Always `await file.read()` — file contents are async. Never use `.file` directly.

## File Structure

```
backend/app/api/endpoints/
├── __init__.py
├── invoices.py    # Upload, list, approve, delete
├── suppliers.py   # Supplier CRUD
└── users.py       # User profile / auth info

backend/app/core/
├── database.py    # Engine, session, get_db
├── security.py    # JWT validation, RoleChecker, get_current_user
└── config.py      # Pydantic Settings (env vars)
```
