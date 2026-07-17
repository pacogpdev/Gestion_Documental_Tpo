import uuid
from datetime import date
from decimal import Decimal

from backend.app.core.config import settings
from backend.app.models.schemas import Invoice, Supplier


def _persist_supplier(db_session, *, name="Delete Supplier"):
    supplier = Supplier(
        id=uuid.uuid4(),
        name=name,
        tax_id=f"TAX-{uuid.uuid4()}",
    )
    db_session.add(supplier)
    db_session.commit()
    return supplier


def _persist_invoice(db_session, supplier_id):
    invoice = Invoice(
        id=uuid.uuid4(),
        supplier_id=supplier_id,
        invoice_number="SUPPLIER-DELETE-001",
        date=date(2024, 10, 5),
        total_amount=Decimal("10.00"),
        currency="EUR",
        status="Pending",
        file_url="/uploads/supplier-delete.pdf",
    )
    db_session.add(invoice)
    db_session.commit()
    return invoice


def test_delete_supplier_without_invoices_returns_success_and_removes_supplier(
    client, db_session
):
    supplier = _persist_supplier(db_session)

    response = client.delete(f"/api/suppliers/{supplier.id}")

    assert response.status_code == 200
    assert response.json() == {"status": "success", "deleted_id": str(supplier.id)}
    assert db_session.get(Supplier, supplier.id) is None


def test_delete_supplier_with_invoices_returns_conflict_and_preserves_supplier(
    client, db_session
):
    supplier = _persist_supplier(db_session, name="Supplier With Invoice")
    _persist_invoice(db_session, supplier.id)

    response = client.delete(f"/api/suppliers/{supplier.id}")

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Cannot delete supplier: 1 invoice(s) associated. Delete the invoices first."
    )
    assert db_session.get(Supplier, supplier.id) is not None


def test_delete_supplier_returns_not_found_for_unknown_supplier(client, db_session):
    supplier_id = uuid.uuid4()

    response = client.delete(f"/api/suppliers/{supplier_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Supplier not found"}


def test_delete_supplier_requires_admin_role(client, db_session, monkeypatch):
    supplier = _persist_supplier(db_session, name="Admin-only Supplier")
    monkeypatch.setattr(settings, "ENTRA_ID_JWKS_URL", "https://example.test/jwks")

    from backend.app.core.security import get_current_user

    app = client.app

    def override_viewer():
        return {"email": "viewer@example.com", "roles": ["Viewer"]}

    app.dependency_overrides[get_current_user] = override_viewer
    try:
        response = client.delete(f"/api/suppliers/{supplier.id}")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
    assert db_session.get(Supplier, supplier.id) is not None
