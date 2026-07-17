# Design: Invoice PDF Cleanup and View

## Technical Approach

Keep the existing FastAPI/SQLAlchemy and React boundaries. The delete route will reuse the injectable `BlobStorageService` and the existing container-aware URL helper, attempt Azure cleanup before the database mutation, then delete line items and the invoice regardless of cleanup outcome. The list response will expose the persisted URL as an additive camelCase field, and `ApprovalDashboard` will render a view action only for non-legacy URLs.

## Architecture Decisions

| Option | Tradeoff | Decision |
|---|---|---|
| Derive the blob name from `file_url` using the configured container prefix | No schema/data migration; rejects paths that do not belong to the configured container. | **Choose.** Parse with `urlparse`, remove the leading slash, require `f"{storage.container_name}/"`, and slice the prefix. For `.../facturas-proveedores/{supplier}/{invoice}/{uuid}.pdf`, pass `{supplier}/{invoice}/{uuid}.pdf` to `delete_blob`. Query strings are excluded by `urlparse`. |
| Store a separate blob-name column | More direct cleanup, but requires migration and backfilling existing invoices. | Reject for this additive change. |
| Delete blob and database row as one transaction | Azure and SQLAlchemy cannot share a transaction; a blob failure could block business deletion. | **Choose best effort.** Capture `invoice.file_url`, skip `/uploads/`, call `delete_blob` inside a broad exception guard, then commit the DB deletion. |
| Add a third-party icon dependency | Adds bundle and maintenance cost for one control. | Use the existing inline SVG style with an eye/document icon, accessible label/title, and a row-specific `data-testid`. |

The existing `get_storage_service` dependency remains the injection boundary used by upload and delete. `BlobStorageService.delete_blob` already swallows Azure SDK failures; the route guard also protects the database operation from mock/client/helper exceptions.

## Data Flow

```text
GET /api/invoices → Invoice query + supplier eager load → InvoiceResponse(fileUrl) → ApprovalDashboard

DELETE /api/invoices/{id}
  → load invoice/file_url → eligible Azure URL? → derive blob name → delete_blob (best effort)
  → delete line items + invoice → commit
```

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/app/api/endpoints/invoices.py` | Modify | Inject storage into DELETE; reuse/clarify container-relative blob extraction; skip legacy paths; perform guarded cleanup before DB deletion; map `file_url` in list responses. |
| `backend/app/models/schemas.py` | Modify | Add `fileUrl: str \| None` to `InvoiceResponse` so missing URLs serialize as `null`. |
| `backend/tests/api/test_invoices.py` | Modify | Add mocked-storage tests for successful deletion, exact blob name, legacy skip, deletion failure, and `fileUrl` serialization. |
| `frontend/src/pages/ApprovalDashboard.tsx` | Modify | Add `fileUrl` to the local invoice type and conditionally render the view-PDF action in the existing Actions cell. |
| `frontend/src/pages/ApprovalDashboard.test.tsx` | Modify | Add MSW invoice fixtures and component tests for eligible, legacy, and null URLs; spy on `window.open`. |
| `frontend/src/pages/ApprovalDashboard.handlers.ts` | Modify | Include representative Azure, `/uploads/`, and null `fileUrl` values in reusable mock data. |

No `frontend/src/api/client.ts` change is required: Axios already returns the additive JSON field without a client-side model layer.

## Interfaces / Contracts

```python
class InvoiceResponse(BaseModel):
    # existing fields...
    fileUrl: str | None
```

The UI eligibility predicate is `Boolean(inv.fileUrl) && !inv.fileUrl.startsWith('/uploads/')`. The enabled button calls `window.open(inv.fileUrl, '_blank')`; it never renders an actionable control for legacy or missing values.

## Testing Strategy

Strict TDD: write RED tests first, then implement the smallest change, then refactor. Backend tests use `app.dependency_overrides[get_storage_service]` with `MagicMock`; no Azure SDK/network calls are allowed. Verify the invoice is absent even when `delete_blob` raises, and verify legacy URLs never call it. Run `cd backend && pytest`. Frontend tests use the existing co-located Vitest/RTL/MSW setup, assert the button’s `data-testid`, and verify `window.open` receives the Azure URL and `_blank`; assert no button for legacy/null data. Run `cd frontend && npm test`.

## Threat Matrix

The HTTP route is modified, but this change does not cross the command, VCS, PR, executable, or process boundaries covered by the matrix:

| Boundary | Applicability | Design response | Planned RED tests |
|---|---|---|---|
| Documentation-like paths | N/A — no document execution/classification. | None. | None. |
| Git repository selection | N/A — no Git operations. | None. | None. |
| Commit state | N/A — SQL commit only, not VCS commit. | None. | None. |
| Push state | N/A — no branch/ref push. | None. | None. |
| PR commands | N/A — no PR automation. | None. | None. |

## Migration / Rollout

No migration required. The response contract is additive, legacy `/uploads/` records remain valid, and the UI hides unsupported links. Roll out backend and frontend together; older clients ignore `fileUrl`.

## Open Questions

- None blocking implementation.
