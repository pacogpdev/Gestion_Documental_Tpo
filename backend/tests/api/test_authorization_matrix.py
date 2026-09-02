from datetime import date
import logging
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from backend.app.core.security import get_current_user
from backend.app.api.endpoints.invoices import get_storage_service
from backend.app.core.config import settings
from backend.app.models.schemas import AuditLog, Invoice, Role, Supplier, User


def _set_user(client, role: str, **claims) -> None:
    client.app.dependency_overrides[get_current_user] = lambda: {
        "email": f"{role.lower()}@example.com",
        "name": f"{role} User",
        "roles": [role],
        **claims,
    }


def _persist_supplier(db_session) -> Supplier:
    supplier = Supplier(id=uuid.uuid4(), name="Acme", tax_id=f"TAX-{uuid.uuid4()}")
    db_session.add(supplier)
    db_session.commit()
    return supplier


def _persist_invoice(db_session, supplier_id) -> Invoice:
    invoice = Invoice(
        id=uuid.uuid4(),
        supplier_id=supplier_id,
        invoice_number="INV-001",
        date=date.today(),
        total_amount=100,
        currency="EUR",
        status="Pending",
        file_url="/uploads/invoice.pdf",
    )
    db_session.add(invoice)
    db_session.commit()
    return invoice


def _use_production_identity(client, monkeypatch, roles):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "AUTH_MODE", "entra")
    client.app.dependency_overrides[get_current_user] = lambda: {
        "tid": "tenant-1", "oid": "oid-1", "preferred_username": "person@example.com",
        "name": "Person", "roles": roles,
    }


def _authorization_event(caplog):
    return next(record for record in caplog.records if record.msg == "authorization.outcome")


def _assert_safe_event(record, outcome, reason, db_session):
    assert (record.outcome, record.reason) == (outcome, reason)
    assert record.correlation_id and db_session.get(AuditLog, uuid.UUID(record.local_audit_id))
    assert not any(hasattr(record, field) for field in ("claims", "email", "secret", "token"))


@pytest.mark.parametrize("role", ["Admin", "Approver", "Clerk", "Viewer"])
def test_all_authenticated_roles_can_read_suppliers(client, role):
    _set_user(client, role)

    response = client.get("/api/suppliers")

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("role", "expected_status"),
    [("Admin", 200), ("Approver", 200), ("Viewer", 200), ("Clerk", 403)],
)
def test_supplier_stats_obey_the_approved_matrix(client, db_session, role, expected_status):
    supplier = _persist_supplier(db_session)
    _set_user(client, role)

    response = client.get(f"/api/suppliers/{supplier.id}/stats")

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["supplierName"] == "Acme"
    else:
        assert response.json() == {"detail": "Insufficient permissions"}


def test_clerk_cannot_delete_an_invoice_or_change_its_state(client, db_session):
    invoice = _persist_invoice(db_session, _persist_supplier(db_session).id)
    _set_user(client, "Clerk")

    response = client.delete(f"/api/invoices/{invoice.id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert db_session.get(Invoice, invoice.id).status == "Pending"


def test_approver_cannot_create_a_supplier(client, db_session):
    _set_user(client, "Approver")

    response = client.post("/api/suppliers", json={"name": "Blocked", "taxId": "BLOCKED"})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert db_session.query(Supplier).filter_by(tax_id="BLOCKED").one_or_none() is None


def test_unauthenticated_approval_does_not_change_an_invoice(client, db_session):
    invoice = _persist_invoice(db_session, _persist_supplier(db_session).id)

    def missing_authorization():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing")

    client.app.dependency_overrides[get_current_user] = missing_authorization
    response = client.patch(f"/api/invoices/{invoice.id}/approve", json={"status": "Approved"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert db_session.get(Invoice, invoice.id).status == "Pending"


def test_me_is_sanitized_and_contains_derived_permissions(client):
    _set_user(client, "Viewer", oid="entra-oid", tid="tenant-id", sub="subject-id")

    response = client.get("/api/users/me")

    assert response.status_code == 200
    assert response.json() == {
        "email": "viewer@example.com",
        "fullName": "Viewer User",
        "roles": ["Viewer"],
        "permissions": ["read", "statistics"],
    }


def test_readiness_is_public_and_does_not_expose_configuration(client):
    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_production_identity_syncs_and_returns_a_sanitized_profile(client, db_session, monkeypatch, caplog):
    db_session.add(Role(id=uuid.uuid4(), name="Viewer"))
    db_session.commit()
    _use_production_identity(client, monkeypatch, ["Viewer"])

    with caplog.at_level(logging.INFO, logger="backend.app.api.dependencies"):
        response = client.get("/api/users/me")

    assert response.json() == {"email": "person@example.com", "fullName": "Person", "roles": ["Viewer"], "permissions": ["read", "statistics"]}
    assert db_session.query(User).filter_by(tenant_id="tenant-1", entra_oid="oid-1").one().roles[0].name == "Viewer"
    _assert_safe_event(_authorization_event(caplog), "authorized", "operation_allowed", db_session)


def test_disabled_production_identity_emits_a_safe_denial(client, db_session, monkeypatch, caplog):
    db_session.add(User(id=uuid.uuid4(), tenant_id="tenant-1", entra_oid="oid-1", is_disabled=True))
    db_session.commit()
    _use_production_identity(client, monkeypatch, ["Viewer"])

    with caplog.at_level(logging.INFO, logger="backend.app.api.dependencies"):
        response = client.get("/api/users/me")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    _assert_safe_event(_authorization_event(caplog), "denied", "identity_disabled", db_session)


def test_production_permission_denial_preserves_business_state_and_emits_a_safe_event(client, db_session, monkeypatch, caplog):
    invoice = _persist_invoice(db_session, _persist_supplier(db_session).id)
    storage = MagicMock()
    client.app.dependency_overrides[get_storage_service] = lambda: storage
    db_session.add(Role(id=uuid.uuid4(), name="Viewer"))
    db_session.commit()
    _use_production_identity(client, monkeypatch, ["Viewer"])

    with caplog.at_level(logging.INFO, logger="backend.app.api.dependencies"):
        response = client.delete(f"/api/invoices/{invoice.id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert db_session.get(Invoice, invoice.id) and db_session.get(Supplier, invoice.supplier_id)
    storage.delete_blob.assert_not_called()
    _assert_safe_event(_authorization_event(caplog), "denied", "operation_denied", db_session)
