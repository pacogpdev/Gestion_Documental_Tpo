import uuid
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import event, inspect, select

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
from backend.migrate_to_azure_sql import (
    TABLE_MIGRATION_ORDER,
    MigrationSummary,
    migrate_database,
)


def manager_for(path):
    return DatabaseManager(db_url=f"sqlite:///{path}")


def populate_source(manager):
    Base.metadata.create_all(manager.engine)
    role_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    user_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    supplier_id = uuid.UUID("33333333-3333-3333-3333-333333333333")
    invoice_id = uuid.UUID("44444444-4444-4444-4444-444444444444")
    line_item_id = uuid.UUID("55555555-5555-5555-5555-555555555555")
    audit_id = uuid.UUID("66666666-6666-6666-6666-666666666666")

    session = manager.get_session()
    session.add_all(
        [
            Role(id=role_id, name="Approver"),
            User(id=user_id, email="migration@example.com", full_name="Migration User"),
            Supplier(
                id=supplier_id,
                name="Migration Supplier",
                tax_id="MIGRATION-TAX",
                email="supplier@example.com",
                address="Migration Avenue 1",
            ),
            Invoice(
                id=invoice_id,
                supplier_id=supplier_id,
                invoice_number="MIG-001",
                date=date(2026, 7, 16),
                total_amount=Decimal("125.50"),
                currency="EUR",
                status="Pending",
                file_url="https://blob.example/mig-001.pdf",
                created_at=datetime(2026, 7, 16, 10, 30),
            ),
            LineItem(
                id=line_item_id,
                invoice_id=invoice_id,
                description="Migration item",
                quantity=Decimal("2.00"),
                unit_price=Decimal("62.75"),
                total_price=Decimal("125.50"),
            ),
            AuditLog(
                id=audit_id,
                user_id=user_id,
                action="created",
                entity_type="invoice",
                entity_id=invoice_id,
                timestamp=datetime(2026, 7, 16, 10, 31),
            ),
        ]
    )
    session.flush()
    session.execute(user_roles.insert().values(user_id=user_id, role_id=role_id))
    session.commit()
    session.close()

    return {
        "role_id": role_id,
        "user_id": user_id,
        "supplier_id": supplier_id,
        "invoice_id": invoice_id,
        "line_item_id": line_item_id,
        "audit_id": audit_id,
    }


def test_migrates_all_tables_preserving_values_and_relationships(tmp_path):
    source = manager_for(tmp_path / "source.sqlite")
    target = manager_for(tmp_path / "target.sqlite")
    identifiers = populate_source(source)
    progress = []

    summary = migrate_database(source, target, progress_callback=progress.append)

    assert isinstance(summary, MigrationSummary)
    assert summary.total_tables == 7
    assert summary.total_rows == 7
    assert progress == [f"{table}: 1 row(s)" for table in TABLE_MIGRATION_ORDER]
    assert set(inspect(target.engine).get_table_names()) == set(TABLE_MIGRATION_ORDER)

    session = target.get_session()
    role = session.get(Role, identifiers["role_id"])
    user = session.get(User, identifiers["user_id"])
    supplier = session.get(Supplier, identifiers["supplier_id"])
    invoice = session.get(Invoice, identifiers["invoice_id"])
    line_item = session.get(LineItem, identifiers["line_item_id"])
    audit_log = session.get(AuditLog, identifiers["audit_id"])
    association = session.execute(select(user_roles)).one()

    assert role.name == "Approver"
    assert user.email == "migration@example.com"
    assert supplier.address == "Migration Avenue 1"
    assert invoice.supplier_id == supplier.id
    assert invoice.total_amount == Decimal("125.50")
    assert line_item.invoice_id == invoice.id
    assert line_item.total_price == Decimal("125.50")
    assert audit_log.user_id == user.id
    assert audit_log.entity_id == invoice.id
    assert association.user_id == user.id
    assert association.role_id == role.id
    session.close()


def test_migration_preserves_fk_order_and_handles_empty_source(tmp_path):
    source = manager_for(tmp_path / "empty-source.sqlite")
    target = manager_for(tmp_path / "empty-target.sqlite")
    progress = []

    summary = migrate_database(source, target, progress_callback=progress.append)

    assert summary == MigrationSummary(total_tables=7, total_rows=0)
    assert progress == [f"{table}: 0 row(s)" for table in TABLE_MIGRATION_ORDER]
    assert set(inspect(target.engine).get_table_names()) == set(TABLE_MIGRATION_ORDER)


def test_failed_copy_rolls_back_the_entire_target_transaction(tmp_path):
    source = manager_for(tmp_path / "failing-source.sqlite")
    target = manager_for(tmp_path / "failing-target.sqlite")
    populate_source(source)

    def fail_on_line_items(connection, cursor, statement, parameters, context, executemany):
        if "INSERT INTO line_items" in statement:
            raise RuntimeError("simulated line item copy failure")

    event.listen(target.engine, "before_cursor_execute", fail_on_line_items)
    try:
        with pytest.raises(RuntimeError, match="simulated line item copy failure"):
            migrate_database(source, target)
    finally:
        event.remove(target.engine, "before_cursor_execute", fail_on_line_items)

    session = target.get_session()
    assert session.query(Role).count() == 0
    assert session.query(User).count() == 0
    assert session.query(Supplier).count() == 0
    assert session.query(Invoice).count() == 0
    assert session.query(LineItem).count() == 0
    assert session.query(AuditLog).count() == 0
    assert session.execute(select(user_roles)).all() == []
    session.close()
