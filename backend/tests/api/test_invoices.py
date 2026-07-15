import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from backend.app.models.schemas import Invoice, Supplier


def test_list_invoices_returns_empty_list_when_no_invoices(client, db_session):
    """TDD Red/Green: Verify that listing invoices returns an empty list initially."""
    response = client.get("/api/invoices")
    assert response.status_code == 200
    assert response.json() == []


def test_list_invoices_returns_existing_invoices(client, db_session):
    """TDD Red/Green: Verify that listing invoices returns populated data."""
    # 1. Arrange: Create a supplier and an invoice in the test database
    supplier_id = uuid.uuid4()
    supplier = Supplier(
        id=supplier_id,
        name="Test Supplier S.A.",
        tax_id="123456789"
    )
    db_session.add(supplier)
    db_session.commit()

    invoice_id = uuid.uuid4()
    invoice = Invoice(
        id=invoice_id,
        supplier_id=supplier_id,
        invoice_number="INV-001",
        date=date(2023, 10, 25),
        total_amount=Decimal("150.50"),
        currency="USD",
        status="Pending",
        file_url="/uploads/test.pdf"
    )
    db_session.add(invoice)
    db_session.commit()

    # 2. Act: Call the endpoint
    response = client.get("/api/invoices")

    # 3. Assert: Verify the response
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 1
    assert data[0]["invoiceNumber"] == "INV-001"
    assert data[0]["supplierName"] == "Test Supplier S.A."
    assert data[0]["totalAmount"] == 150.5
    assert data[0]["currency"] == "USD"
    assert data[0]["status"] == "Pending"


def test_upload_duplicate_invoice_number_same_supplier_returns_409(client, db_session):
    """Verify that uploading an invoice with the same invoice_number + supplier_id returns 409."""
    # 1. Arrange: Create a supplier and an invoice via DB
    supplier_id = uuid.uuid4()
    supplier = Supplier(
        id=supplier_id,
        name="Acme Corp",
        tax_id="TAX-ACME-001"
    )
    db_session.add(supplier)
    db_session.commit()

    existing_invoice = Invoice(
        id=uuid.uuid4(),
        supplier_id=supplier_id,
        invoice_number="FAC-2024-001",
        date=date(2024, 3, 15),
        total_amount=Decimal("1250.00"),
        currency="EUR",
        status="Pending",
        file_url="/uploads/existing.pdf"
    )
    db_session.add(existing_invoice)
    db_session.commit()

    # 2. Mock AI extraction to return the same invoice_number + same tax_id
    extraction_result = {
        "tax_id": "TAX-ACME-001",
        "supplier_name": "Acme Corp",
        "invoice_number": "FAC-2024-001",
        "date": date(2024, 3, 15),
        "total_amount": 1250.0,
        "currency": "EUR",
        "line_items": [
            {"description": "Service", "quantity": 1, "unit_price": 1250.0, "total_price": 1250.0}
        ]
    }

    with patch("backend.app.api.endpoints.invoices.extract_invoice_data", return_value=extraction_result):
        response = client.post(
            "/api/invoices/upload",
            files={"file": ("duplicate.pdf", b"dummy content", "application/pdf")}
        )

    # 3. Assert: 409 Conflict with meaningful detail
    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "FAC-2024-001" in data["detail"]
    assert "Acme Corp" in data["detail"]
    assert "already exists" in data["detail"].lower()


def test_upload_duplicate_invoice_number_different_supplier_allowed(client, db_session):
    """Verify that the same invoice_number is allowed for a different supplier."""
    # 1. Arrange: Create supplier A + invoice
    supplier_a_id = uuid.uuid4()
    supplier_a = Supplier(id=supplier_a_id, name="Supplier A", tax_id="TAX-A-001")
    db_session.add(supplier_a)
    db_session.commit()

    existing = Invoice(
        id=uuid.uuid4(),
        supplier_id=supplier_a_id,
        invoice_number="FAC-2024-001",
        date=date(2024, 1, 10),
        total_amount=Decimal("500.00"),
        currency="EUR",
        status="Pending",
        file_url="/uploads/a.pdf"
    )
    db_session.add(existing)
    db_session.commit()

    # 2. Act: Upload same invoice_number but for supplier B (different tax_id)
    extraction_result = {
        "tax_id": "TAX-B-001",  # different supplier
        "supplier_name": "Supplier B",
        "invoice_number": "FAC-2024-001",  # same number
        "date": date(2024, 2, 20),
        "total_amount": 300.0,
        "currency": "EUR",
        "line_items": []
    }

    with patch("backend.app.api.endpoints.invoices.extract_invoice_data", return_value=extraction_result):
        response = client.post(
            "/api/invoices/upload",
            files={"file": ("b.pdf", b"dummy", "application/pdf")}
        )

    # 3. Assert: 200 OK (allows duplicate number for different supplier)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_upload_exact_same_file_twice_returns_409(client, db_session):
    """Upload the same file twice → second attempt should return 409."""
    extraction_result = {
        "tax_id": "TAX-UNIQUE",
        "supplier_name": "Unique Supplier",
        "invoice_number": "UNIQUE-INV",
        "date": date(2024, 6, 1),
        "total_amount": 100.0,
        "currency": "USD",
        "line_items": []
    }

    with patch("backend.app.api.endpoints.invoices.extract_invoice_data", return_value=extraction_result):
        # First upload — should succeed
        first = client.post(
            "/api/invoices/upload",
            files={"file": ("same.pdf", b"same content", "application/pdf")}
        )
        assert first.status_code == 200

        # Second upload — should fail with 409
        second = client.post(
            "/api/invoices/upload",
            files={"file": ("same.pdf", b"same content", "application/pdf")}
        )
        assert second.status_code == 409
        assert "already exists" in second.json()["detail"].lower()


# ── Edge case tests for duplicate-invoice restriction ──

def test_edge_case_1_case_sensitivity(client, db_session):
    """#1 — invoice_number is case-insensitive (normalized to uppercase)."""
    extraction = {
        "tax_id": "TAX-CASE", "supplier_name": "Case Supplier",
        "invoice_number": "abc-001", "date": date(2024, 1, 1),
        "total_amount": 100.0, "currency": "EUR", "line_items": []
    }
    with patch("backend.app.api.endpoints.invoices.extract_invoice_data", return_value=extraction):
        resp1 = client.post("/api/invoices/upload", files={"file": ("a.pdf", b"x", "application/pdf")})
        assert resp1.status_code == 200

    # Same invoice_number but uppercase — should be caught as duplicate
    extraction["invoice_number"] = "ABC-001"
    with patch("backend.app.api.endpoints.invoices.extract_invoice_data", return_value=extraction):
        resp2 = client.post("/api/invoices/upload", files={"file": ("b.pdf", b"x", "application/pdf")})
        assert resp2.status_code == 409
        assert "ABC-001" in resp2.json()["detail"]


def test_edge_case_2_rejected_does_not_block(client, db_session):
    """#2 — Replaced: Rejected invoice is replaced on re-upload with same number."""
    supplier_id = uuid.uuid4()
    db_session.add(Supplier(id=supplier_id, name="Rejected Co", tax_id="TAX-REJ"))
    db_session.commit()

    # Create a Rejected invoice directly in the DB
    inv_id = uuid.uuid4()
    db_session.add(Invoice(
        id=inv_id, supplier_id=supplier_id, invoice_number="REJ-001",
        date=date(2024, 5, 5), total_amount=Decimal("200"), currency="EUR",
        status="Rejected", file_url="/uploads/rejected.pdf"
    ))
    db_session.commit()

    # Now upload the same number again (should replace)
    extraction = {
        "tax_id": "TAX-REJ", "supplier_name": "Rejected Co",
        "invoice_number": "REJ-001", "date": date(2024, 6, 1),
        "total_amount": 250.0, "currency": "EUR", "line_items": []
    }
    with patch("backend.app.api.endpoints.invoices.extract_invoice_data", return_value=extraction):
        resp = client.post("/api/invoices/upload", files={"file": ("new.pdf", b"x", "application/pdf")})
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    # The old Rejected invoice should be gone, only the new Pending one exists
    invoices = db_session.query(Invoice).all()
    assert len(invoices) == 1
    assert invoices[0].status == "Pending"
    assert float(invoices[0].total_amount) == 250.0


def test_edge_case_4_unknown_tax_id_same_name_shares_supplier(client, db_session):
    """#4 — No tax_id extracted but same name → same supplier record."""
    extraction = {
        # no tax_id
        "supplier_name": "Mystery Vendor",
        "invoice_number": "MYS-001", "date": date(2024, 7, 7),
        "total_amount": 150.0, "currency": "USD", "line_items": []
    }
    with patch("backend.app.api.endpoints.invoices.extract_invoice_data", return_value=extraction):
        resp1 = client.post("/api/invoices/upload", files={"file": ("a.pdf", b"x", "application/pdf")})
        assert resp1.status_code == 200

        # Same name, same number → 409 (same supplier, duplicate)
        resp2 = client.post("/api/invoices/upload", files={"file": ("b.pdf", b"x", "application/pdf")})
        assert resp2.status_code == 409

    # Both uploads mapped to the same supplier
    suppliers = db_session.query(Supplier).filter(Supplier.name == "Mystery Vendor").all()
    assert len(suppliers) == 1


def test_edge_case_4_unknown_tax_id_different_names_different_suppliers(client, db_session):
    """#4 — No tax_id, different names → different suppliers, same invoice_number allowed."""
    extraction = {
        "supplier_name": "Vendor Alpha",
        "invoice_number": "SAME-NUM", "date": date(2024, 8, 8),
        "total_amount": 100.0, "currency": "EUR", "line_items": []
    }
    with patch("backend.app.api.endpoints.invoices.extract_invoice_data", return_value=extraction):
        resp1 = client.post("/api/invoices/upload", files={"file": ("a.pdf", b"x", "application/pdf")})
        assert resp1.status_code == 200

    extraction["supplier_name"] = "Vendor Beta"
    with patch("backend.app.api.endpoints.invoices.extract_invoice_data", return_value=extraction):
        resp2 = client.post("/api/invoices/upload", files={"file": ("b.pdf", b"x", "application/pdf")})
        assert resp2.status_code == 200  # different supplier → allowed

    # Two different suppliers created
    alphas = db_session.query(Supplier).filter(Supplier.name == "Vendor Alpha").all()
    betas = db_session.query(Supplier).filter(Supplier.name == "Vendor Beta").all()
    assert len(alphas) == 1
    assert len(betas) == 1


def test_edge_case_5_whitespace_trim(client, db_session):
    """#5 — Invoice numbers with leading/trailing spaces match after trim."""
    extraction = {
        "tax_id": "TAX-TRIM", "supplier_name": "Trim Supplier",
        "invoice_number": "  TRIM-001  ", "date": date(2024, 9, 9),
        "total_amount": 100.0, "currency": "EUR", "line_items": []
    }
    with patch("backend.app.api.endpoints.invoices.extract_invoice_data", return_value=extraction):
        resp1 = client.post("/api/invoices/upload", files={"file": ("a.pdf", b"x", "application/pdf")})
        assert resp1.status_code == 200

    # Same invoice_number without spaces → duplicate
    extraction["invoice_number"] = "TRIM-001"
    with patch("backend.app.api.endpoints.invoices.extract_invoice_data", return_value=extraction):
        resp2 = client.post("/api/invoices/upload", files={"file": ("b.pdf", b"x", "application/pdf")})
        assert resp2.status_code == 409

    # Verify the stored invoice_number is trimmed and uppercase
    invoice = db_session.query(Invoice).first()
    assert invoice.invoice_number == "TRIM-001"