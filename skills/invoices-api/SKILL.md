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

## Structural Context (CodeGraph)

> Derived from the CodeGraph index (653 nodes, 1,321 edges). Use for impact analysis before edits.

### Hub symbols in this area
| Symbol | Location | Callers | Tests | Note |
|--------|----------|---------|-------|------|
| `get_db` | database.py | all endpoints | conftest.py ✅ | #1 cross-cutting dep — every endpoint depends on it |
| `get_current_user` | security.py:72 | 6 (invoices, suppliers, users) | test_supplier_stats.py, conftest.py ✅ | Auth hub |
| `RoleChecker` | security.py:87 | 2 (invoices, suppliers) | ⚠️ no direct test | RBAC guard — only transitively tested |
| `upload_invoice` | invoices.py:132 | 0 (HTTP entry) | test_invoices.py ✅ | Upload flow entry point |
| `_resolve_supplier` | invoices.py:22 | 1 (upload_invoice) | indirect | Supplier resolution with 3-tier tax_id fallback |
| `_normalize_invoice_number` | invoices.py:57 | 1 (upload_invoice) | indirect | Trim + uppercase normalization |
| `_cleanup_uploaded_blob` | invoices.py:89 | 2 (upload_invoice failure, delete_invoice) | indirect | Compensatory blob cleanup |
| `_sas_url_for_invoice` | invoices.py:110 | 1 (list_invoices) | indirect | Per-invoice SAS with try/except |

### Call paths through this area
```
POST /invoices/upload (upload_invoice, invoices.py:132)
  → extract_invoice_data (ai_service.py:128)       [10 callers — AI hub]
  → _resolve_supplier (invoices.py:22)              [3-tier tax_id fallback]
  → _normalize_invoice_number (invoices.py:57)      [trim + uppercase]
  → storage.upload_pdf → StorageUploadError (5 callers)
  → db.flush + db.commit
  → except IntegrityError → _cleanup_uploaded_blob   [race-condition safety]

GET /invoices (list_invoices, invoices.py:238)
  → selectinload(Invoice.supplier)
  → _sas_url_for_invoice per row                     [one failure skips, doesn't break list]

DELETE /invoices/{id} (delete_invoice, invoices.py:280)
  → delete LineItems (FK constraint)
  → delete Invoice
  → db.commit
  → _cleanup_uploaded_blob                            [best-effort, AFTER commit]
```

### Per-symbol test coverage
- `upload_invoice`: covered by `backend/tests/api/test_invoices.py` ✅ (upload flow, 503 on failure, duplicate 409)
- `delete_invoice`: covered by `backend/tests/api/test_invoices.py` ✅ (blob cleanup after commit)
- `list_invoices`: covered by `backend/tests/api/test_invoices.py` ✅
- `RoleChecker`: ⚠️ no direct test — only exercised transitively via endpoint tests
- `get_current_user`: covered by `backend/tests/api/test_supplier_stats.py` + `conftest.py` ✅
- `suppliers.py` endpoints: covered by `backend/tests/api/test_supplier_stats.py` ✅ (stats)
- `users.py` `get_current_user_profile`: ⚠️ no direct backend test found

### Cross-layer dependencies
- **409 duplicate error** originates from 3 layers: explicit check in `upload_invoice` (line 159) → DB constraint `uq_supplier_invoice` (schemas.py:68) → `except IntegrityError` catch (line 219). All three must remain in sync.
- **`InvoiceResponse` Pydantic model** (schemas.py:116) is the canonical API contract — frontend `Invoice` interface (ApprovalDashboard.tsx:5) must match its fields. Drift here breaks the dashboard silently.
- **`_sas_url_for_invoice`** bridges API layer → storage layer; one failure per row is logged and skipped (dashboard stays usable).
- **`RoleChecker(["Clerk", "Admin"])`** on upload/delete — but frontend `UserRole` type omits 'Clerk'. Not a security hole (backend enforces), but a type-consistency gap.

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
