import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CHAR, create_engine
from sqlalchemy.dialects import mssql
from sqlalchemy.orm import sessionmaker

from backend.app.models.schemas import GUID, Invoice, Supplier


def test_guid_uses_char_36_for_sqlite(sqlite_dialect):
    implementation = GUID().load_dialect_impl(sqlite_dialect)

    assert isinstance(implementation, CHAR)
    assert implementation.length == 36


def test_guid_uses_uniqueidentifier_for_mssql(mssql_dialect):
    implementation = GUID().load_dialect_impl(mssql_dialect)

    assert isinstance(implementation, mssql.UNIQUEIDENTIFIER)


def test_guid_binds_mssql_values_as_canonical_strings(mssql_dialect):
    identifier = uuid.uuid4()

    assert GUID().process_bind_param(identifier, mssql_dialect) == str(identifier)
    assert GUID().process_bind_param(str(identifier), mssql_dialect) == str(identifier)


def test_guid_result_values_are_uuid_instances(sqlite_dialect):
    identifier = uuid.uuid4()

    assert GUID().process_result_value(str(identifier), sqlite_dialect) == identifier
    assert GUID().process_result_value(identifier, sqlite_dialect) is identifier


def test_uuid_ids_and_foreign_keys_round_trip_on_sqlite():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Supplier.metadata.create_all(engine)
    Invoice.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    supplier_id = uuid.uuid4()
    invoice_id = uuid.uuid4()

    supplier = Supplier(id=supplier_id, name="Round Trip Supplier", tax_id="ROUND-TRIP")
    invoice = Invoice(
        id=invoice_id,
        supplier=supplier,
        invoice_number="ROUND-TRIP-001",
        date=date(2026, 7, 16),
        total_amount=Decimal("42.50"),
        currency="EUR",
        status="Pending",
        file_url="/uploads/round-trip.pdf",
    )
    session.add(invoice)
    session.commit()

    loaded_invoice = session.get(Invoice, invoice_id)

    assert loaded_invoice.id == invoice_id
    assert isinstance(loaded_invoice.id, uuid.UUID)
    assert loaded_invoice.supplier_id == supplier_id
    assert isinstance(loaded_invoice.supplier_id, uuid.UUID)
    assert loaded_invoice.supplier.id == supplier_id
    assert loaded_invoice.supplier.name == "Round Trip Supplier"

    session.close()
    Invoice.metadata.drop_all(engine)
    Supplier.metadata.drop_all(engine)
    engine.dispose()
