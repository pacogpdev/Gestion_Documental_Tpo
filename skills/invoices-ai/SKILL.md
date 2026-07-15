---
name: invoices-ai
description: >
  Azure AI Content Understanding integration for invoice extraction.
  Client initialization, dev mode fallback, field extraction helpers, field mapping,
  line items, MIME detection, error handling.
  Trigger: When editing backend/app/services/ai_service.py, extracting invoice data
  via AI, modifying field mapping or extraction logic.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Editing `backend/app/services/ai_service.py`
- Adding or modifying extraction field mapping
- Handling AI extraction errors or edge cases
- Modifying dev-mode fallback extraction
- Changing MIME type detection
- Working with line item extraction

## Critical Patterns

### Client initialization

Always use the `get_ai_client()` helper — it handles endpoint/key resolution and returns `None` when Azure is not configured:

```python
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.ai.contentunderstanding.models import AnalysisInput
from azure.core.credentials import AzureKeyCredential
from backend.app.core.config import settings

def get_ai_client() -> ContentUnderstandingClient | None:
    endpoint = settings.AZURE_CONTENT_ENDPOINT or settings.AZURE_AI_ENDPOINT
    api_key = settings.AZURE_CONTENT_KEY or settings.AZURE_AI_KEY
    if not endpoint or not api_key:
        return None
    return ContentUnderstandingClient(
        endpoint,
        AzureKeyCredential(api_key),
    )
```

Endpoint format: `https://{resource}.services.ai.azure.com/`

### Dev mode fallback

When Azure is not configured, the system returns **mock data** derived from the filename so the upload flow can be tested end-to-end:

```python
def _extract_dev_mode(filename: str) -> dict:
    stem = Path(filename).stem.replace("factura_", "").replace("invoice_", "")
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
            {"description": "Servicio de Consultoría", "quantity": 5, "unit_price": 200.00, "total_price": 1000.00},
            {"description": "Licencia de Software",   "quantity": 2, "unit_price": 250.00, "total_price": 500.00},
        ],
    }
```

- Always generate unique UUID-based `invoice_number` and `tax_id` to avoid DB constraint collisions
- The date is always `date.today()` so tests are deterministic within a session

### Field extraction helpers

The SDK exposes typed accessors on each `ContentField`. Use the helpers instead of raw access:

**`_get_value(field)`** — Extract primitive value from any field type:

```python
def _get_value(field):
    if field is None:
        return None
    # Check order: string → number → date → integer
    if hasattr(field, 'value_string') and field.value_string is not None:
        return field.value_string
    if hasattr(field, 'value_number') and field.value_number is not None:
        return field.value_number
    if hasattr(field, 'value_date') and field.value_date is not None:
        return field.value_date
    if hasattr(field, 'value_integer') and field.value_integer is not None:
        return field.value_integer
    return None
```

**`_extract_amount(field, default=0.0)`** — Extract amount from either a NumberField (direct) or an ObjectField with `Amount` sub-field:

```python
def _extract_amount(field, default: float = 0.0) -> float:
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
```

**`_extract_currency(field, default="EUR")`** — Extract currency code from an ObjectField:

```python
def _extract_currency(field, default: str = "EUR") -> str:
    if field is None:
        return default
    if hasattr(field, 'value_object') and field.value_object is not None:
        ccy = field.value_object.get("CurrencyCode")
        if ccy is not None and hasattr(ccy, 'value_string') and ccy.value_string is not None:
            return ccy.value_string
    return default
```

**`_detect_mime_type(filename)`** — Map file extension to MIME:

```python
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
```

### Main extraction pipeline

```python
async def extract_invoice_data(file_stream, filename: str = "invoice.pdf"):
    client = get_ai_client()
    if client is None:
        return _extract_dev_mode(filename)   # ← dev mode shortcut

    file_bytes: bytes = file_stream.read() if hasattr(file_stream, 'read') else file_stream
    mime_type = _detect_mime_type(filename)

    poller = client.begin_analyze(
        analyzer_id="prebuilt-invoice",
        inputs=[AnalysisInput(data=file_bytes, mime_type=mime_type)],
    )
    result = poller.result()

    if not result.contents:
        return _extract_dev_mode(filename)   # ← AI returned nothing

    content = result.contents[0]
    fields: dict = content.fields if content.fields else {}
```

**Critical**: Use `AnalysisInput(data=file_bytes, mime_type=mime_type)`, not `data=bytes, mime_type=...` or file paths. The SDK accepts raw bytes directly — no signed URLs needed.

### Field mapping (result → dict)

| Extracted field | AI field name(s) | Helper | Detail |
|---|---|---|---|
| `invoice_number` | `InvoiceId` | `_get_value()` | |
| `date` | `InvoiceDate` | direct `.value_date` | `date_field.value_date` (not through `_get_value`) |
| `total_amount` | `TotalAmount`, `InvoiceTotal` | `_extract_amount()` | May be NumberField or ObjectField with Amount |
| `currency` | from TotalAmount object | `_extract_currency()` | Extracted from the same field as amount |
| `tax_amount` | `TotalTaxAmount`, `TotalTax`, `TaxDetails[]`, `(TotalAmount - SubtotalAmount)` | `_extract_amount()` | Multiple fallbacks (see below) |
| `tax_id` | `VendorTaxId` | `_get_value()` | |
| `supplier_name` | `VendorName` | `.value_string`.replace("\n", " ") | Sanitize newlines Azure sometimes inserts |
| `line_items` | `LineItems`, fallback: `Items` | see below | |

**Tax amount fallback chain:**

1. `TotalTaxAmount` or `TotalTax` field (direct)
2. `TaxDetails[]` — sum all `Amount` values from the array
3. `SubtotalAmount` and `TotalAmount` — estimate as `TotalAmount - SubtotalAmount`
4. `0.0` — if none of the above yield a value

### Line items

```python
items_field = fields.get("LineItems") or fields.get("Items")
if items_field is not None and hasattr(items_field, 'value_array') and items_field.value_array is not None:
    for item in items_field.value_array:
        if not hasattr(item, 'value_object') or item.value_object is None:
            continue
        item_obj = item.value_object
        description = _get_value(item_obj.get("Description")) or "Unknown"
        quantity = _extract_amount(item_obj.get("Quantity"), 1.0)
        unit_price = _extract_amount(item_obj.get("UnitPrice"), 0.0)
        total_price = _extract_amount(
            item_obj.get("TotalAmount") or item_obj.get("Amount"), 0.0
        )
```

**Field name fallbacks per line item:**

| Desired field | Primary AI field | Fallback |
|---|---|---|
| `description` | `Description` | `"Unknown"` |
| `quantity` | `Quantity` | `1.0` |
| `unit_price` | `UnitPrice` | `0.0` |
| `total_price` | `TotalAmount` | `Amount`, `0.0` |

### Error handling

```python
try:
    # extraction logic
except HTTPException:
    raise
except Exception as e:
    raise HTTPException(status_code=500, detail=f"AI Extraction failed: {str(e)}")
```

- Re-raise HTTPExceptions as-is (they're intentional, like 409 from duplicate detection)
- Wrap all other exceptions in a 500 with descriptive message
- The AI service does NOT handle DB operations — it returns a dict; the endpoint handles persistence

### Configuration

In `backend/app/core/config.py`:

| Setting | Purpose | Fallback |
|---|---|---|
| `AZURE_CONTENT_ENDPOINT` | Content Understanding endpoint | `AZURE_AI_ENDPOINT` |
| `AZURE_CONTENT_KEY` | Content Understanding API key | `AZURE_AI_KEY` |

When both `AZURE_CONTENT_ENDPOINT` and `AZURE_AI_ENDPOINT` are empty → dev mode (mock data).

## File Structure

```
backend/app/
├── services/
│   └── ai_service.py         # Extraction logic — this skill's territory
├── core/
│   └── config.py             # AZURE_CONTENT_ENDPOINT / AZURE_CONTENT_KEY settings
```
