import uuid
from calendar import monthrange
from datetime import date
from decimal import Decimal

import pytest

from backend.app.core.config import settings
from backend.app.core.security import get_current_user
from backend.app.main import app
from backend.app.models.schemas import Invoice, LineItem, Supplier


def _month_start(months_ago: int) -> date:
    month_index = date.today().year * 12 + date.today().month - 1 - months_ago
    year, month_zero_based = divmod(month_index, 12)
    return date(year, month_zero_based + 1, 1)


def _invoice_date(months_ago: int, day: int = 15) -> date:
    month_start = _month_start(months_ago)
    return month_start.replace(day=min(day, monthrange(month_start.year, month_start.month)[1]))


def _persist_supplier(db_session, *, name: str, tax_id: str | None = None) -> Supplier:
    supplier = Supplier(
        id=uuid.uuid4(),
        name=name,
        tax_id=tax_id or f"TAX-{uuid.uuid4()}",
    )
    db_session.add(supplier)
    db_session.commit()
    return supplier


def _persist_invoice(
    db_session,
    supplier_id,
    *,
    number: str,
    months_ago: int,
    amount: str,
    status: str = "Pending",
    currency: str = "EUR",
    descriptions: list[tuple[str, str]] | None = None,
) -> Invoice:
    invoice = Invoice(
        id=uuid.uuid4(),
        supplier_id=supplier_id,
        invoice_number=number,
        date=_invoice_date(months_ago),
        total_amount=Decimal(amount),
        currency=currency,
        status=status,
        file_url=f"/uploads/{number}.pdf",
    )
    db_session.add(invoice)
    db_session.flush()
    for description, total_price in descriptions or []:
        db_session.add(
            LineItem(
                id=uuid.uuid4(),
                invoice_id=invoice.id,
                description=description,
                quantity=Decimal("1"),
                unit_price=Decimal(total_price),
                total_price=Decimal(total_price),
            )
        )
    db_session.commit()
    return invoice


def _set_role(client, monkeypatch, role: str) -> None:
    monkeypatch.setattr(settings, "ENTRA_ID_JWKS_URL", "https://example.test/jwks")
    client.app.dependency_overrides[get_current_user] = lambda: {
        "email": f"{role.lower()}@example.com",
        "roles": [role],
    }


def _expected_months() -> list[str]:
    return [
        _month_start(months_ago).strftime("%Y-%m")
        for months_ago in range(11, -1, -1)
    ]


def test_supplier_stats_returns_all_metrics_for_trailing_year(client, db_session):
    supplier = _persist_supplier(db_session, name="Acme Corp", tax_id="TAX-ACME")
    other_supplier = _persist_supplier(db_session, name="Other Corp")
    _persist_invoice(
        db_session,
        supplier.id,
        number="ACME-001",
        months_ago=1,
        amount="1200.00",
        status="Approved",
        descriptions=[("Hosting", "700.00"), ("Support", "500.00")],
    )
    _persist_invoice(
        db_session,
        supplier.id,
        number="ACME-002",
        months_ago=2,
        amount="800.00",
        status="Rejected",
        descriptions=[("Hosting", "300.00"), ("Support", "500.00")],
    )
    _persist_invoice(
        db_session,
        supplier.id,
        number="ACME-003",
        months_ago=3,
        amount="400.00",
        status="Pending",
        descriptions=[("Hosting", "400.00")],
    )
    _persist_invoice(
        db_session,
        supplier.id,
        number="ACME-OUTSIDE",
        months_ago=13,
        amount="999.00",
        status="Approved",
        descriptions=[("Outside window", "999.00")],
    )
    _persist_invoice(
        db_session,
        other_supplier.id,
        number="OTHER-001",
        months_ago=0,
        amount="1000.00",
        status="Approved",
    )

    response = client.get(f"/api/suppliers/{supplier.id}/stats")

    assert response.status_code == 200
    assert response.json() == {
        "supplierName": "Acme Corp",
        "taxId": "TAX-ACME",
        "totalInvoices": 3,
        "totalAmount": 2400.0,
        "currency": "EUR",
        "monthlyAmounts": [
            {"month": month, "amount": amount}
            for month, amount in zip(_expected_months(), [0.0] * 8 + [400.0, 800.0, 1200.0, 0.0])
        ],
        "annualAccumulated": 2400.0,
        "annualPercentage": pytest.approx(2400 / 3400 * 100),
        "grandTotalAllSuppliers": 3400.0,
        "topLineItems": [
            {"description": "Hosting", "totalAmount": 1400.0, "invoiceCount": 3},
            {"description": "Support", "totalAmount": 1000.0, "invoiceCount": 2},
        ],
        "statusDistribution": {"Approved": 1, "Rejected": 1, "Pending": 1},
        "averageInvoiceAmount": 800.0,
        "topInvoice": {"number": "ACME-001", "amount": 1200.0},
    }


def test_supplier_stats_returns_twelve_ordered_months_with_zero_fill(client, db_session):
    supplier = _persist_supplier(db_session, name="Monthly Supplier")
    _persist_invoice(
        db_session,
        supplier.id,
        number="MONTH-001",
        months_ago=11,
        amount="125.50",
    )
    _persist_invoice(
        db_session,
        supplier.id,
        number="MONTH-002",
        months_ago=0,
        amount="374.50",
    )

    response = client.get(f"/api/suppliers/{supplier.id}/stats")

    assert response.status_code == 200
    months = response.json()["monthlyAmounts"]
    assert [entry["month"] for entry in months] == _expected_months()
    assert months[0]["amount"] == 125.5
    assert months[-1]["amount"] == 374.5
    assert sum(entry["amount"] for entry in months) == 500.0


def test_supplier_stats_returns_zero_values_for_supplier_without_invoices(client, db_session):
    supplier = _persist_supplier(db_session, name="Empty Supplier")

    response = client.get(f"/api/suppliers/{supplier.id}/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["totalInvoices"] == 0
    assert body["totalAmount"] == 0.0
    assert body["annualAccumulated"] == 0.0
    assert body["annualPercentage"] == 0.0
    assert body["grandTotalAllSuppliers"] == 0.0
    assert body["averageInvoiceAmount"] == 0.0
    assert body["monthlyAmounts"] == [
        {"month": month, "amount": 0.0} for month in _expected_months()
    ]
    assert body["topLineItems"] == []
    assert body["statusDistribution"] == {"Approved": 0, "Rejected": 0, "Pending": 0}
    assert body["topInvoice"] is None


def test_supplier_stats_calculates_percentage_against_all_suppliers(client, db_session):
    supplier = _persist_supplier(db_session, name="Percentage Supplier")
    other_supplier = _persist_supplier(db_session, name="Grand Total Supplier")
    _persist_invoice(
        db_session,
        supplier.id,
        number="PERCENT-001",
        months_ago=1,
        amount="1200.00",
    )
    _persist_invoice(
        db_session,
        other_supplier.id,
        number="PERCENT-002",
        months_ago=1,
        amount="1800.00",
    )

    response = client.get(f"/api/suppliers/{supplier.id}/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["grandTotalAllSuppliers"] == 3000.0
    assert body["annualPercentage"] == pytest.approx(40.0)


def test_supplier_stats_returns_top_ten_line_items_ordered_by_total(client, db_session):
    supplier = _persist_supplier(db_session, name="Line Item Supplier")
    descriptions = [
        (f"Item {index:02d}", f"{index * 10}.00")
        for index in range(1, 13)
    ]
    _persist_invoice(
        db_session,
        supplier.id,
        number="ITEMS-001",
        months_ago=1,
        amount="1000.00",
        descriptions=descriptions,
    )
    _persist_invoice(
        db_session,
        supplier.id,
        number="ITEMS-002",
        months_ago=1,
        amount="1000.00",
        descriptions=[("Item 12", "100.00"), ("Item 11", "50.00")],
    )

    response = client.get(f"/api/suppliers/{supplier.id}/stats")

    assert response.status_code == 200
    top_items = response.json()["topLineItems"]
    assert len(top_items) == 10
    assert [item["description"] for item in top_items] == [
        "Item 12",
        "Item 11",
        "Item 10",
        "Item 09",
        "Item 08",
        "Item 07",
        "Item 06",
        "Item 05",
        "Item 04",
        "Item 03",
    ]
    assert top_items[0] == {
        "description": "Item 12",
        "totalAmount": 220.0,
        "invoiceCount": 2,
    }
    assert top_items[-1]["totalAmount"] == 30.0


def test_supplier_stats_counts_all_supported_statuses(client, db_session):
    supplier = _persist_supplier(db_session, name="Status Supplier")
    for index, status in enumerate(["Approved", "Approved", "Rejected", "Pending"]):
        _persist_invoice(
            db_session,
            supplier.id,
            number=f"STATUS-{index}",
            months_ago=index,
            amount="100.00",
            status=status,
        )

    response = client.get(f"/api/suppliers/{supplier.id}/stats")

    assert response.status_code == 200
    assert response.json()["statusDistribution"] == {
        "Approved": 2,
        "Rejected": 1,
        "Pending": 1,
    }


def test_supplier_stats_returns_not_found_for_unknown_supplier(client):
    response = client.get(f"/api/suppliers/{uuid.uuid4()}/stats")

    assert response.status_code == 404
    assert response.json() == {"detail": "Supplier not found"}


@pytest.mark.parametrize(
    ("role", "expected_status"),
    [("Admin", 200), ("Approver", 200), ("Clerk", 403), ("Viewer", 403)],
)
def test_supplier_stats_enforces_admin_and_approver_roles(
    client, db_session, monkeypatch, role, expected_status
):
    supplier = _persist_supplier(db_session, name="Role Supplier")
    _set_role(client, monkeypatch, role)

    try:
        response = client.get(f"/api/suppliers/{supplier.id}/stats")
    finally:
        client.app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["supplierName"] == "Role Supplier"
    else:
        assert response.json() == {"detail": "Insufficient permissions"}
