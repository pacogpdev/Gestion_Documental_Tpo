"""Create the configured database schema and seed repeatable fixture data."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

# Support both ``python -m backend.seed_db`` and ``python backend/seed_db.py``
# from the project root.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.app.core.database import Base, DatabaseManager
from backend.app.models.schemas import (
    AuditLog,
    Invoice,
    LineItem,
    Role,
    Supplier,
    User,
    user_roles,
)


ROLE_NAMES = ("Admin", "Approver", "Clerk", "Viewer")
USER_FIXTURES = (
    ("admin@example.com", "Admin User", "Admin"),
    ("approver@example.com", "Approver User", "Approver"),
    ("clerk@example.com", "Clerk User", "Clerk"),
    ("viewer@example.com", "Viewer User", "Viewer"),
)


def _get_or_create_role(session, name: str) -> Role:
    role = session.query(Role).filter_by(name=name).one_or_none()
    if role is None:
        role = Role(name=name)
        session.add(role)
        session.flush()
        print(f"[OK]  Role created: {name}.")
    else:
        print(f"[..]  Role already exists -- skipped: {name}.")
    return role


def _get_or_create_user(session, email: str, full_name: str, role: Role) -> User:
    user = session.query(User).filter_by(email=email).one_or_none()
    if user is None:
        user = User(email=email, full_name=full_name)
        session.add(user)
        session.flush()
        print(f"[OK]  User created: {email}.")
    else:
        print(f"[..]  User already exists -- skipped: {email}.")

    if role not in user.roles:
        user.roles.append(role)
        session.flush()
    return user


def _get_or_create_supplier(session, values: dict) -> Supplier:
    supplier = session.query(Supplier).filter_by(tax_id=values["tax_id"]).one_or_none()
    if supplier is None:
        supplier = Supplier(**values)
        session.add(supplier)
        session.flush()
        print(f"[OK]  Supplier created: {values['name']}.")
    else:
        print(f"[..]  Supplier already exists -- skipped: {values['name']}.")
    return supplier


def _get_or_create_invoice(session, supplier: Supplier, values: dict) -> Invoice:
    invoice = (
        session.query(Invoice)
        .filter_by(invoice_number=values["invoice_number"], supplier_id=supplier.id)
        .one_or_none()
    )
    if invoice is None:
        invoice = Invoice(supplier_id=supplier.id, **values)
        session.add(invoice)
        session.flush()
        print(f"[OK]  Invoice created: {values['invoice_number']}.")
    else:
        print(f"[..]  Invoice already exists -- skipped: {values['invoice_number']}.")
    return invoice


def _seed_fixture_data(session) -> None:
    roles = {name: _get_or_create_role(session, name) for name in ROLE_NAMES}
    for email, full_name, role_name in USER_FIXTURES:
        _get_or_create_user(session, email, full_name, roles[role_name])

    suppliers = (
        {
            "name": "Proveedor Global SA",
            "tax_id": "12345678-//",
        },
        {
            "name": "Tech Solutions SRL",
            "tax_id": "87654321-//",
        },
    )
    supplier_records = {
        values["tax_id"]: _get_or_create_supplier(session, values)
        for values in suppliers
    }

    invoice_values = (
        (
            "12345678-//",
            {
                "invoice_number": "FAC-2026-001",
                "date": date(2026, 1, 1),
                "total_amount": 1250.00,
                "currency": "USD",
                "status": "Pending",
                "file_url": "/invoices/FAC-2026-001.pdf",
            },
            (("Suministros de Oficina", 10, 50.00, 500.00),),
        ),
        (
            "87654321-//",
            {
                "invoice_number": "FAC-2026-002",
                "date": date(2026, 1, 2),
                "total_amount": 3400.00,
                "currency": "EUR",
                "status": "Pending",
                "file_url": "/invoices/FAC-2026-002.pdf",
            },
            (("Servidores Cloud", 3, 800.00, 2400.00),),
        ),
    )
    for tax_id, values, line_items in invoice_values:
        invoice = _get_or_create_invoice(session, supplier_records[tax_id], values)
        if session.query(LineItem).filter_by(invoice_id=invoice.id).count() == 0:
            for description, quantity, unit_price, total_price in line_items:
                session.add(
                    LineItem(
                        invoice_id=invoice.id,
                        description=description,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price,
                    )
                )
            session.flush()


def seed_data(db_manager: DatabaseManager | None = None) -> None:
    """Create all tables and commit all fixture data as one transaction.

    When no manager is supplied, ``DatabaseManager`` reads ``DATABASE_URL``
    from application settings. Passing a manager keeps the same logic usable
    for temporary SQLite databases and integration tests.
    """

    manager = db_manager or DatabaseManager()
    Base.metadata.create_all(bind=manager.engine)
    session = manager.get_session()
    try:
        with session.begin():
            _seed_fixture_data(session)
        print("\n[DONE]  Database seeded successfully!")
    except Exception:
        session.rollback()
        print("\n[FAIL]  Seeding failed -- transaction rolled back.")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_data()
