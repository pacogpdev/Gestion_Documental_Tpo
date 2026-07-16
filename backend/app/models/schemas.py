import uuid
from datetime import date, datetime
from pydantic import BaseModel
from sqlalchemy import Column, String, ForeignKey, DateTime, Date, Numeric, Table, TypeDecorator, CHAR, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship

from backend.app.core.database import Base

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        elif dialect.name == 'mssql':
            return UNIQUEIDENTIFIER()
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        elif dialect.name == 'mssql':
            return str(value if isinstance(value, uuid.UUID) else uuid.UUID(value))
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

# Many-to-Many Link for Users and Roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", GUID(), ForeignKey("users.id"), primary_key=True),
    Column("role_id", GUID(), ForeignKey("roles.id"), primary_key=True),
)

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    tax_id = Column(String(50), unique=True, nullable=False)
    email = Column(String(255))
    address = Column(String)
    invoices = relationship("Invoice", back_populates="supplier")

class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        # Unique constraint as safety net against race conditions
        UniqueConstraint('supplier_id', 'invoice_number', name='uq_supplier_invoice'),
    )
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(GUID(), ForeignKey("suppliers.id"))
    invoice_number = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(20), default="Pending") # Pending, Approved, Rejected
    file_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    supplier = relationship("Supplier", back_populates="invoices")
    line_items = relationship("LineItem", back_populates="invoice", cascade="all, delete-orphan")

class LineItem(Base):
    __tablename__ = "line_items"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(GUID(), ForeignKey("invoices.id", ondelete="CASCADE"))
    description = Column(String)
    quantity = Column(Numeric(12, 2))
    unit_price = Column(Numeric(12, 2))
    total_price = Column(Numeric(12, 2))
    
    invoice = relationship("Invoice", back_populates="line_items")

class Role(Base):
    __tablename__ = "roles"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False) # Admin, Approver, Viewer

class User(Base):
    __tablename__ = "users"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255))
    roles = relationship("Role", secondary=user_roles)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(GUID(), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class InvoiceResponse(BaseModel):
    """Pydantic response model for Invoice with camelCase fields."""
    id: str
    invoiceNumber: str
    supplierName: str
    date: date
    totalAmount: float
    currency: str
    status: str

    class Config:
        from_attributes = True
