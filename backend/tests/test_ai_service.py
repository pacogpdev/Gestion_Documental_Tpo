from unittest.mock import MagicMock, patch
from datetime import date
import pytest
from fastapi import HTTPException
from backend.app.services.ai_service import extract_invoice_data


# ── Test helpers ──────────────────────────────────────────────────────────


def _mock_string(value: str) -> MagicMock:
    """Create a mock StringField-like object."""
    f = MagicMock()
    f.value_string = value
    f.value_number = None
    f.value_date = None
    f.value_object = None
    f.value_array = None
    f.value_integer = None
    return f


def _mock_number(value: float) -> MagicMock:
    """Create a mock NumberField-like object."""
    f = MagicMock()
    f.value_number = value
    f.value_string = None
    f.value_date = None
    f.value_object = None
    f.value_array = None
    f.value_integer = None
    return f


def _mock_date(value: date) -> MagicMock:
    """Create a mock DateField-like object."""
    f = MagicMock()
    f.value_date = value
    f.value_string = None
    f.value_number = None
    f.value_object = None
    f.value_array = None
    f.value_integer = None
    return f


def _mock_currency(amount: float, currency: str = "EUR") -> MagicMock:
    """Create a mock ObjectField that looks like a currency (Amount + CurrencyCode)."""
    f = MagicMock()
    f.value_object = {
        "Amount": _mock_number(amount),
        "CurrencyCode": _mock_string(currency),
    }
    f.value_number = None
    f.value_string = None
    f.value_date = None
    f.value_array = None
    f.value_integer = None
    return f


def _mock_line_item(
    description: str,
    quantity: float,
    unit_price: float,
    total_price: float,
    currency: str = "EUR",
) -> MagicMock:
    """Create a mock line-item object (ObjectField with Description, Quantity, UnitPrice,
    Amount/TotalAmount)."""
    item = MagicMock()
    item.value_object = {
        "Description": _mock_string(description),
        "Quantity": _mock_number(quantity),
        "UnitPrice": _mock_currency(unit_price, currency),
        "Amount": _mock_currency(total_price, currency),
    }
    return item


def _mock_array(items: list) -> MagicMock:
    """Create a mock ArrayField-like object."""
    f = MagicMock()
    f.value_array = items
    f.value_string = None
    f.value_number = None
    f.value_date = None
    f.value_object = None
    f.value_integer = None
    return f


# ── Fixture ───────────────────────────────────────────────────────────────


@pytest.fixture
def mock_ai_client():
    with patch("backend.app.services.ai_service.get_ai_client") as mock_get:
        mock_client = MagicMock()
        mock_get.return_value = mock_client
        yield mock_client


# ── Tests ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_extract_invoice_data_happy_path(mock_ai_client):
    """Scenario: Happy path extraction. Verify that valid AI response is parsed correctly."""
    # Build fields dict matching the Content Understanding prebuilt-invoice structure
    fields = {
        "InvoiceId": _mock_string("INV-123"),
        "InvoiceDate": _mock_date(date(2023, 10, 27)),
        "InvoiceTotal": _mock_currency(110.0, "EUR"),
        "TotalTax": _mock_currency(10.0, "EUR"),
        "VendorName": _mock_string("Test Supplier"),
        "VendorTaxId": _mock_string("TAX-001"),
        "Items": _mock_array([
            _mock_line_item("Item 1", 1.0, 100.0, 100.0, "EUR"),
        ]),
    }

    # Build result: poller -> result -> contents[0] -> fields
    mock_poller = MagicMock()
    mock_result = MagicMock()
    mock_content = MagicMock()
    mock_content.fields = fields
    mock_result.contents = [mock_content]
    mock_poller.result.return_value = mock_result
    mock_ai_client.begin_analyze.return_value = mock_poller

    result = await extract_invoice_data(MagicMock())

    assert result["invoice_number"] == "INV-123"
    assert result["date"] == date(2023, 10, 27)
    assert result["total_amount"] == 110.0
    assert result["currency"] == "EUR"
    assert result["tax_amount"] == 10.0
    assert result["supplier_name"] == "Test Supplier"
    assert result["tax_id"] == "TAX-001"
    assert len(result["line_items"]) == 1
    assert result["line_items"][0]["description"] == "Item 1"
    assert result["line_items"][0]["quantity"] == 1.0
    assert result["line_items"][0]["unit_price"] == 100.0
    assert result["line_items"][0]["total_price"] == 100.0


@pytest.mark.asyncio
async def test_extract_invoice_data_no_documents(mock_ai_client):
    """Scenario: No contents found. System falls back to dev-mode extraction."""
    mock_poller = MagicMock()
    mock_result = MagicMock()
    mock_result.contents = []
    mock_poller.result.return_value = mock_result
    mock_ai_client.begin_analyze.return_value = mock_poller

    result = await extract_invoice_data(MagicMock())

    assert result["invoice_number"].startswith("DEV-")
    assert result["total_amount"] == 1500.0
    assert len(result["line_items"]) == 2


@pytest.mark.asyncio
async def test_extract_invoice_data_missing_optional_fields(mock_ai_client):
    """Scenario: Missing optional fields. System should populate with defaults and not crash."""
    fields = {
        "InvoiceId": _mock_string("INV-MIN"),
    }

    mock_poller = MagicMock()
    mock_result = MagicMock()
    mock_content = MagicMock()
    mock_content.fields = fields
    mock_result.contents = [mock_content]
    mock_poller.result.return_value = mock_result
    mock_ai_client.begin_analyze.return_value = mock_poller

    result = await extract_invoice_data(MagicMock())

    assert result["invoice_number"] == "INV-MIN"
    assert result["date"] is None
    assert result["total_amount"] == 0.0
    assert result["line_items"] == []
    assert result["supplier_name"] is None


@pytest.mark.asyncio
async def test_extract_invoice_data_sdk_exception(mock_ai_client):
    """Scenario: SDK failure. System MUST return a 500 error."""
    mock_ai_client.begin_analyze.side_effect = Exception("Network Timeout")

    with pytest.raises(HTTPException) as excinfo:
        await extract_invoice_data(MagicMock())

    assert excinfo.value.status_code == 500
    assert "AI Extraction failed: Network Timeout" in excinfo.value.detail


@pytest.mark.asyncio
async def test_extract_line_items_content_understanding_format(mock_ai_client):
    """Scenario: Content Understanding uses 'LineItems' field name (not 'Items')."""
    fields = {
        "InvoiceId": _mock_string("INV-CU"),
        "InvoiceTotal": _mock_currency(200.0, "USD"),
        "LineItems": _mock_array([
            _mock_line_item("Product A", 2.0, 50.0, 100.0, "USD"),
            _mock_line_item("Product B", 3.0, 25.0, 75.0, "USD"),
        ]),
    }

    mock_poller = MagicMock()
    mock_result = MagicMock()
    mock_content = MagicMock()
    mock_content.fields = fields
    mock_result.contents = [mock_content]
    mock_poller.result.return_value = mock_result
    mock_ai_client.begin_analyze.return_value = mock_poller

    result = await extract_invoice_data(MagicMock())

    assert result["invoice_number"] == "INV-CU"
    assert result["currency"] == "USD"
    assert result["total_amount"] == 200.0
    assert len(result["line_items"]) == 2
    assert result["line_items"][0]["description"] == "Product A"
    assert result["line_items"][0]["quantity"] == 2.0
    assert result["line_items"][0]["unit_price"] == 50.0
    assert result["line_items"][0]["total_price"] == 100.0
    assert result["line_items"][1]["description"] == "Product B"


@pytest.mark.asyncio
async def test_supplier_name_newline_sanitization(mock_ai_client):
    """Scenario: Supplier name contains newlines. They should be stripped/replaced."""
    fields = {
        "VendorName": _mock_string("FROCA Int\nS.L.U."),
        "InvoiceId": _mock_string("INV-NL"),
        "InvoiceTotal": _mock_currency(100.0),
    }

    mock_poller = MagicMock()
    mock_result = MagicMock()
    mock_content = MagicMock()
    mock_content.fields = fields
    mock_result.contents = [mock_content]
    mock_poller.result.return_value = mock_result
    mock_ai_client.begin_analyze.return_value = mock_poller

    result = await extract_invoice_data(MagicMock())

    assert result["supplier_name"] == "FROCA Int S.L.U."


@pytest.mark.asyncio
async def test_empty_fields_does_not_crash(mock_ai_client):
    """Scenario: Content has no fields (None or empty dict). Should not crash."""
    mock_poller = MagicMock()
    mock_result = MagicMock()
    mock_content = MagicMock()
    mock_content.fields = {}
    mock_result.contents = [mock_content]
    mock_poller.result.return_value = mock_result
    mock_ai_client.begin_analyze.return_value = mock_poller

    result = await extract_invoice_data(MagicMock())

    # All fields should be None/defaults
    assert result["invoice_number"] is None
    assert result["total_amount"] == 0.0
    assert result["line_items"] == []
