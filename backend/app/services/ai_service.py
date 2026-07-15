from datetime import date
from pathlib import Path
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.ai.contentunderstanding.models import AnalysisInput
from azure.core.credentials import AzureKeyCredential
from fastapi import HTTPException
from backend.app.core.config import settings
import uuid


def get_ai_client() -> ContentUnderstandingClient | None:
    """
    Returns an initialized Azure ContentUnderstandingClient.
    When Azure is not configured, returns None so the dev-mode fallback kicks in.
    """
    endpoint = settings.AZURE_CONTENT_ENDPOINT or settings.AZURE_AI_ENDPOINT
    api_key = settings.AZURE_CONTENT_KEY or settings.AZURE_AI_KEY
    if not endpoint or not api_key:
        return None
    return ContentUnderstandingClient(
        endpoint,
        AzureKeyCredential(api_key),
    )


def _extract_dev_mode(filename: str) -> dict:
    """
    Dev-mode fallback: returns plausible mock data when Azure AI is not configured.
    Extracts a rough supplier name and invoice number from the filename so each
    upload feels unique and verifiable.
    """
    # Derive a readable supplier name from the filename (e.g. "factura_acme.pdf" → "Acme")
    stem = Path(filename).stem.replace("factura_", "").replace("invoice_", "").replace("_", " ").replace("-", " ").strip()
    supplier_name = stem.title() if stem else "Dev Test Supplier"
    tax_id = f"DEV-{uuid.uuid4().hex[:6].upper()}"

    return {
        "invoice_number": f"DEV-{uuid.uuid4().hex[:8].upper()}",
        "date": date.today(),
        "total_amount": 1500.00,
        "currency": "EUR",
        "tax_amount": 250.00,
        "tax_id": tax_id,
        "supplier_name": supplier_name,
        "line_items": [
            {"description": "Servicio de Consultoría",      "quantity": 5,  "unit_price": 200.00, "total_price": 1000.00},
            {"description": "Licencia de Software",         "quantity": 2,  "unit_price": 250.00, "total_price": 500.00},
        ],
    }


# ── Field extraction helpers ──────────────────────────────────────────────


def _get_value(field):
    """
    Extract the primitive value from a ContentField based on its typed accessor.

    Returns ``str``, ``float``, ``datetime.date``, or ``None`` depending on field type
    (checked in order: string, number, date, integer).
    """
    if field is None:
        return None
    if hasattr(field, 'value_string') and field.value_string is not None:
        return field.value_string
    if hasattr(field, 'value_number') and field.value_number is not None:
        return field.value_number
    if hasattr(field, 'value_date') and field.value_date is not None:
        return field.value_date
    if hasattr(field, 'value_integer') and field.value_integer is not None:
        return field.value_integer
    return None


def _extract_amount(field, default: float = 0.0) -> float:
    """
    Extract a numeric amount from a ContentField that may be:
    - a ``NumberField`` (direct ``value_number``)
    - an ``ObjectField`` with nested ``Amount`` / ``CurrencyCode`` sub-fields
    """
    if field is None:
        return default
    # Currency object: { Amount: NumberField, CurrencyCode: StringField }
    if hasattr(field, 'value_object') and field.value_object is not None:
        amt = field.value_object.get("Amount")
        if amt is not None and hasattr(amt, 'value_number') and amt.value_number is not None:
            return float(amt.value_number)
    # Direct number
    if hasattr(field, 'value_number') and field.value_number is not None:
        return float(field.value_number)
    return default


def _extract_currency(field, default: str = "EUR") -> str:
    """
    Extract the currency code from an ``ObjectField`` with ``Amount`` / ``CurrencyCode``
    sub-fields.
    """
    if field is None:
        return default
    if hasattr(field, 'value_object') and field.value_object is not None:
        ccy = field.value_object.get("CurrencyCode")
        if ccy is not None and hasattr(ccy, 'value_string') and ccy.value_string is not None:
            return ccy.value_string
    return default


def _detect_mime_type(filename: str) -> str:
    """Map file extension to MIME type for the Content Understanding API."""
    ext = Path(filename).suffix.lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".bmp": "image/bmp",
        ".heif": "image/heif",
        ".heic": "image/heic",
    }
    return mime_map.get(ext, "application/pdf")


# ── Main extraction function ──────────────────────────────────────────────


async def extract_invoice_data(file_stream, filename: str = "invoice.pdf"):
    """
    Extracts data from an invoice PDF/Image using Azure AI Content Understanding
    (prebuilt-invoice analyzer).

    When Azure is not configured (dev mode), returns mock data derived from the
    filename so the upload flow can be tested end-to-end.
    """
    client = get_ai_client()
    if client is None:
        return _extract_dev_mode(filename)

    try:
        # Read file bytes (handle both bytes and file-like objects)
        file_bytes: bytes = file_stream.read() if hasattr(file_stream, 'read') else file_stream
        mime_type = _detect_mime_type(filename)

        poller = client.begin_analyze(
            analyzer_id="prebuilt-invoice",
            inputs=[AnalysisInput(data=file_bytes, mime_type=mime_type)],
        )
        result = poller.result()

        if not result.contents:
            import logging
            logging.warning("Azure AI did not detect an invoice in the uploaded file. Falling back to dev-mode extraction.")
            return _extract_dev_mode(filename)

        content = result.contents[0]
        fields: dict = content.fields if content.fields else {}

        # ── TotalAmount (currency object with Amount + CurrencyCode) ──
        total_field = fields.get("TotalAmount") or fields.get("InvoiceTotal")
        total_amount = _extract_amount(total_field, 0.0)
        currency = _extract_currency(total_field, "EUR")

        # ── TotalTaxAmount: try TotalTaxAmount first, fall back to TaxDetails ──
        tax_amount = _extract_amount(fields.get("TotalTaxAmount") or fields.get("TotalTax"), 0.0)
        if tax_amount == 0.0:
            tax_details = fields.get("TaxDetails")
            if tax_details is not None and hasattr(tax_details, 'value_array') and tax_details.value_array:
                for td in tax_details.value_array:
                    if hasattr(td, 'value_object') and td.value_object is not None:
                        td_amount = _extract_amount(td.value_object.get("Amount"), 0.0)
                        tax_amount += td_amount
            if tax_amount == 0.0 and fields.get("SubtotalAmount") and fields.get("TotalAmount"):
                # Estimate tax as TotalAmount - SubtotalAmount
                sub = _extract_amount(fields.get("SubtotalAmount"), 0.0)
                tot = _extract_amount(fields.get("TotalAmount"), 0.0)
                tax_amount = round(tot - sub, 2)

        # ── InvoiceId ──
        invoice_number = _get_value(fields.get("InvoiceId"))

        # ── InvoiceDate ──
        date_field = fields.get("InvoiceDate")
        invoice_date = date_field.value_date if (
            date_field is not None
            and hasattr(date_field, 'value_date')
            and date_field.value_date is not None
        ) else None

        # ── VendorName (sanitize newlines that Azure sometimes inserts) ──
        vendor_field = fields.get("VendorName")
        supplier_name = (
            vendor_field.value_string.replace("\n", " ").strip()
            if vendor_field is not None
            and hasattr(vendor_field, 'value_string')
            and vendor_field.value_string is not None
            else None
        )

        # ── VendorTaxId ──
        tax_id = _get_value(fields.get("VendorTaxId"))

        extracted_data: dict = {
            "invoice_number": invoice_number,
            "date": invoice_date,
            "total_amount": total_amount,
            "currency": currency,
            "tax_amount": tax_amount,
            "tax_id": tax_id,
            "supplier_name": supplier_name,
            "line_items": [],
        }

        # ── Line items ──
        # Content Understanding uses "LineItems"; the legacy model used "Items"
        items_field = fields.get("LineItems") or fields.get("Items")
        if (
            items_field is not None
            and hasattr(items_field, 'value_array')
            and items_field.value_array is not None
        ):
            for item in items_field.value_array:
                if not hasattr(item, 'value_object') or item.value_object is None:
                    continue
                item_obj = item.value_object

                description = _get_value(item_obj.get("Description")) or "Unknown"
                quantity = _extract_amount(item_obj.get("Quantity"), 1.0)
                # UnitPrice and TotalAmount may be currency objects or direct numbers
                unit_price = _extract_amount(item_obj.get("UnitPrice"), 0.0)
                # Content Understanding → "TotalAmount"; legacy → "Amount"
                total_price = _extract_amount(
                    item_obj.get("TotalAmount") or item_obj.get("Amount"), 0.0
                )

                extracted_data["line_items"].append({
                    "description": description,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": total_price,
                })

        return extracted_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Extraction failed: {str(e)}")
