"""
Seed script for the invoice dashboard database.

Populates the SQLite database with sample data for development/demo use.
Safe to run multiple times — uses existence checks to avoid duplicates.
"""

import sys
from pathlib import Path
from datetime import date

# Ensure the project root is on sys.path so we can import backend.app.*
# The script lives at backend/seed_db.py, so root = this file's grandparent
# (backend/ -> PROYECTO_FACTURAS_PROVEEDORES/)
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# ── App imports ──────────────────────────────────────────────────────────────
from backend.app.core.database import DatabaseManager, Base
from backend.app.models.schemas import Supplier, Invoice, LineItem

# Build the SQLite URL with an explicit path relative to this script's position.
# The app creates test.db in backend/test.db (relative to where the .env lives).
# We resolve it explicitly so the seed always lands in the same place regardless
# of the working directory from which the script is invoked.
DB_DIR = Path(__file__).resolve().parent
DB_URL = f"sqlite:///{DB_DIR / 'test.db'}"


def seed_data() -> None:
    """Run the seeding logic inside a single transaction."""
    db_manager = DatabaseManager(db_url=DB_URL)

    # Ensure tables exist (safe no-op if they already do)
    Base.metadata.create_all(bind=db_manager.engine)

    session = db_manager.get_session()
    try:
        # ── 1. Supplier ──────────────────────────────────────────────────
        supplier = session.query(Supplier).filter_by(tax_id="12345678-//").first()
        if supplier is None:
            supplier = Supplier(
                name="Proveedor Global SA",
                tax_id="12345678-//",
            )
            session.add(supplier)
            session.flush()  # materialise the PK so we can reference it
            print("[OK]  Supplier created.")
        else:
            print("[..]  Supplier already exists -- skipped.")

        # ── 2. Second Supplier ─────────────────────────────────────────
        supplier_2 = session.query(Supplier).filter_by(tax_id="87654321-//").first()
        if supplier_2 is None:
            supplier_2 = Supplier(
                name="Tech Solutions SRL",
                tax_id="87654321-//",
            )
            session.add(supplier_2)
            session.flush()
            print("[OK]  Supplier 2 created.")
        else:
            print("[..]  Supplier 2 already exists -- skipped.")

        # ── 4. Fourth Supplier ─────────────────────────────────────────
        supplier_4 = session.query(Supplier).filter_by(tax_id="11223344-//").first()
        if supplier_4 is None:
            supplier_4 = Supplier(
                name="Global Logistics Ltd",
                tax_id="11223344-//",
                email="contact@globallogistics.com",
                address="Port Road 10, Singapore",
            )
            session.add(supplier_4)
            session.flush()
            print("[OK]  Supplier 4 created.")
        else:
            print("[..]  Supplier 4 already exists -- skipped.")

        # ── 5. Invoice #4 (Global Logistics) ──────────────────────────
        invoice_4 = (
            session.query(Invoice)
            .filter_by(invoice_number="FAC-2026-004")
            .first()
        )
        if invoice_4 is None:
            invoice_4 = Invoice(
                supplier_id=supplier_4.id,
                invoice_number="FAC-2026-004",
                date=date.today(),
                total_amount=1200.00,
                currency="USD",
                status="Pending",
                file_url="/invoices/FAC-2026-004.pdf",
            )
            session.add(invoice_4)
            session.flush()
            print("[OK]  Invoice #4 created.")
        else:
            print("[..]  Invoice #4 already exists -- skipped.")

        # ── 6. Invoice #1 (Proveedor Global) ──────────────────────────
        invoice = (
            session.query(Invoice)
            .filter_by(invoice_number="FAC-2026-001")
            .first()
        )
        if invoice is None:
            invoice = Invoice(
                supplier_id=supplier.id,
                invoice_number="FAC-2026-001",
                date=date.today(),
                total_amount=1250.00,
                currency="USD",
                status="Pending",
                file_url="/invoices/FAC-2026-001.pdf",
            )
            session.add(invoice)
            session.flush()
            print("[OK]  Invoice #1 created.")
        else:
            print("[..]  Invoice #1 already exists -- skipped.")

        # ── 4. Invoice #2 (Tech Solutions) ────────────────────────────
        invoice_2 = (
            session.query(Invoice)
            .filter_by(invoice_number="FAC-2026-002")
            .first()
        )
        if invoice_2 is None:
            invoice_2 = Invoice(
                supplier_id=supplier_2.id,
                invoice_number="FAC-2026-002",
                date=date.today(),
                total_amount=3400.00,
                currency="EUR",
                status="Pending",
                file_url="/invoices/FAC-2026-002.pdf",
            )
            session.add(invoice_2)
            session.flush()
            print("[OK]  Invoice #2 created.")
        else:
            print("[..]  Invoice #2 already exists -- skipped.")

        # ── 4b. Third Supplier (sin factura para probar búsqueda) ────
        supplier_3 = session.query(Supplier).filter_by(tax_id="55556666-//").first()
        if supplier_3 is None:
            supplier_3 = Supplier(
                name="Distribuidora Austral SRL",
                tax_id="55556666-//",
                email="facturas@distribuidora-austral.com",
                address="Av. Corrientes 2045, CABA",
            )
            session.add(supplier_3)
            session.flush()
            print("[OK]  Supplier 3 created.")
        else:
            print("[..]  Supplier 3 already exists -- skipped.")

        # ── 5. Invoice #3 (Distribuidora Austral) ───────────────────
        invoice_3 = (
            session.query(Invoice)
            .filter_by(invoice_number="FAC-2026-003")
            .first()
        )
        if invoice_3 is None:
            invoice_3 = Invoice(
                supplier_id=supplier_3.id,
                invoice_number="FAC-2026-003",
                date=date.today(),
                total_amount=890.50,
                currency="ARS",
                status="Pending",
                file_url="/invoices/FAC-2026-003.pdf",
            )
            session.add(invoice_3)
            session.flush()
            print("[OK]  Invoice #3 created.")
        else:
            print("[..]  Invoice #3 already exists -- skipped.")

        # ── 6. Line Items for Invoice #1 ────────────────────────────
        existing_count = (
            session.query(LineItem).filter_by(invoice_id=invoice.id).count()
        )
        if existing_count == 0:
            items = [
                {"description": "Suministros de Oficina",   "quantity": 10, "unit_price": 50.00,  "total_price": 500.00},
                {"description": "Soporte Técnico",          "quantity": 5,  "unit_price": 100.00, "total_price": 500.00},
                {"description": "Servicio de Consultoría",  "quantity": 1,  "unit_price": 250.00, "total_price": 250.00},
            ]
            for data in items:
                session.add(LineItem(invoice_id=invoice.id, **data))
            print("[OK]  3 line items for Invoice #1 created.")
        else:
            print(f"[..]  {existing_count} line item(s) for Invoice #1 already exist -- skipped.")

        # ── 7. Line Items for Invoice #2 ────────────────────────────
        existing_count_2 = (
            session.query(LineItem).filter_by(invoice_id=invoice_2.id).count()
        )
        if existing_count_2 == 0:
            items_2 = [
                {"description": "Servidores Cloud",         "quantity": 3,  "unit_price": 800.00,  "total_price": 2400.00},
                {"description": "Licencias Anuales",        "quantity": 10, "unit_price": 100.00,  "total_price": 1000.00},
            ]
            for data in items_2:
                session.add(LineItem(invoice_id=invoice_2.id, **data))
            print("[OK]  2 line items for Invoice #2 created.")
        else:
            print(f"[..]  {existing_count_2} line item(s) for Invoice #2 already exist -- skipped.")

        # ── 8. Line Items for Invoice #3 ────────────────────────────
        existing_count_3 = (
            session.query(LineItem).filter_by(invoice_id=invoice_3.id).count()
        )
        if existing_count_3 == 0:
            items_3 = [
                {"description": "Equipamiento de Oficina",   "quantity": 5,  "unit_price": 120.00,  "total_price": 600.00},
                {"description": "Servicio de Mensajería",    "quantity": 1,  "unit_price": 290.50,  "total_price": 290.50},
            ]
            for data in items_3:
                session.add(LineItem(invoice_id=invoice_3.id, **data))
            print("[OK]  2 line items for Invoice #3 created.")
        else:
            print(f"[..]  {existing_count_3} line item(s) for Invoice #3 already exist -- skipped.")

        # ── 9. Line Items for Invoice #4 ────────────────────────────
        existing_count_4 = (
            session.query(LineItem).filter_by(invoice_id=invoice_4.id).count()
        )
        if existing_count_4 == 0:
            items_4 = [
                {"description": "Transporte Marítimo",      "quantity": 1,  "unit_price": 800.00,  "total_price": 800.00},
                {"description": "Seguro de Carga",           "quantity": 1,  "unit_price": 400.00,  "total_price": 400.00},
            ]
            for data in items_4:
                session.add(LineItem(invoice_id=invoice_4.id, **data))
            print("[OK]  2 line items for Invoice #4 created.")
        else:
            print(f"[..]  {existing_count_4} line item(s) for Invoice #4 already exist -- skipped.")

        session.commit()
        print("\n[DONE]  Database seeded successfully!")

    except Exception:
        session.rollback()
        print("\n[FAIL]  Seeding failed -- transaction rolled back.")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_data()
