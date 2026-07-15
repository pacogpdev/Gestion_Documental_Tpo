---
name: invoices-db
description: >
  SQLAlchemy model patterns for invoices, suppliers, and users. Schema conventions, GUID primary keys, relationships, constraints.
  Trigger: When editing files in backend/app/models/, backend/app/core/database.py, or adding/modifying database operations.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Adding or modifying SQLAlchemy models in `backend/app/models/schemas.py`
- Writing database queries in endpoint files
- Configuring database engine or session in `backend/app/core/database.py`
- Adding constraints or relationships

## Critical Patterns

### Model base and engine

All models use `declarative_base()` from `backend/app/core/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()
```

### GUID primary key (cross-database compatible)

Use the custom `GUID` type for all primary and foreign keys. It works on both SQLite and PostgreSQL:

```python
from sqlalchemy import Column, String, ForeignKey, TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value
```

### Model convention

```python
from sqlalchemy import Column, String, ForeignKey, DateTime, Date, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.schemas import GUID

class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint('supplier_id', 'invoice_number', name='uq_supplier_invoice'),
    )
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(GUID(), ForeignKey("suppliers.id"))
    invoice_number = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(20), default="Pending")
    file_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier", back_populates="invoices")
    line_items = relationship("LineItem", back_populates="invoice", cascade="all, delete-orphan")
```

### Relationship conventions

| Type | Pattern |
|------|---------|
| Many-to-One | `supplier = relationship("Supplier", back_populates="invoices")` on the child |
| One-to-Many | `invoices = relationship("Invoice", back_populates="supplier")` on the parent |
| Cascade delete | `cascade="all, delete-orphan"` on the parent's relationship to children |
| FK cascade | `ForeignKey("invoices.id", ondelete="CASCADE")` on the child column |

### Many-to-Many with association table

```python
from sqlalchemy import Table

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", GUID(), ForeignKey("users.id"), primary_key=True),
    Column("role_id", GUID(), ForeignKey("roles.id"), primary_key=True),
)
```

### Query patterns in endpoints

Use eager loading with `selectinload` to avoid N+1:

```python
from sqlalchemy.orm import selectinload

invoices = db.query(Invoice).options(selectinload(Invoice.supplier)).all()
```

### DB session dependency

Always use the `get_db` dependency — never create sessions manually:

```python
from backend.app.core.database import get_db

def list_invoices(db: Session = Depends(get_db)):
    return db.query(Invoice).all()
```

### Error handling and rollback

Wrap commits to catch race conditions:

```python
try:
    db.commit()
except IntegrityError:
    db.rollback()
    raise HTTPException(status_code=409, detail="Duplicate entry")
```

### Supplier resolution pattern

```python
supplier = db.query(Supplier).filter(Supplier.tax_id == tax_id).first()
if not supplier:
    supplier = Supplier(id=uuid.uuid4(), name=supplier_name, tax_id=tax_id)
    db.add(supplier)
    db.flush()  # Assign ID before adding dependent records
elif supplier.name != supplier_name:
    supplier.name = supplier_name
    db.flush()
```

Always call `db.flush()` after adding a new supplier if you need its ID immediately.

### Invoice status lifecycle

| Status | Meaning | Allowed transitions |
|--------|---------|---------------------|
| `Pending` | Awaiting review | → Approved, → Rejected |
| `Approved` | Approved by Approver | Terminal |
| `Rejected` | Rejected by Clerk | Deleted on re-upload |

### File Structure

```
backend/app/
├── models/
│   └── schemas.py     # All SQLAlchemy models + Pydantic response models
├── core/
│   └── database.py    # Engine, DatabaseManager, get_db dependency
```
