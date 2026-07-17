# Tasks: Invoice PDF Cleanup and View

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 80–120 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Backend cleanup and response contract | PR 1 | `cd backend && pytest tests/api/test_invoices.py` | `pytest` API client with mocked storage | Revert `invoices.py`, `schemas.py`, and backend tests |
| 2 | PDF view action | PR 1 | `cd frontend && npm test -- ApprovalDashboard` | Vitest + RTL + MSW; no browser harness needed | Revert dashboard, handler, and component tests |

## Phase 1: RED Tests (strict TDD)

- [x] 1.1 In `backend/tests/api/test_invoices.py`, add a mocked-storage deletion test asserting an Azure URL derives the exact container-relative blob name and the invoice is removed.
- [x] 1.2 Add the legacy `/uploads/` deletion test asserting the database row is removed and `delete_blob` is never called.
- [x] 1.3 Add the cleanup-failure test with `delete_blob.side_effect`, asserting DELETE still succeeds and the invoice is absent.
- [x] 1.4 Add response-contract tests asserting Azure URLs are preserved in `fileUrl` and `InvoiceResponse` serializes a missing URL as JSON `null`.
- [x] 1.5 In `ApprovalDashboard.test.tsx` and `.handlers.ts`, add Azure, legacy, and null fixtures; assert only eligible rows render `view-pdf-btn-{id}` and clicking it calls `window.open(url, '_blank')`.

## Phase 2: GREEN Implementation

- [x] 2.1 In `backend/app/models/schemas.py` and `backend/app/api/endpoints/invoices.py`, add optional `fileUrl` and map each stored `file_url` in `GET /api/invoices`.
- [x] 2.2 In `backend/app/api/endpoints/invoices.py`, inject `get_storage_service` into DELETE, skip `/uploads/`, derive the configured-container-relative name with URL parsing, guard `delete_blob` broadly, then delete line items and invoice.
- [x] 2.3 In `frontend/src/pages/ApprovalDashboard.tsx`, add `fileUrl` to `Invoice` and render an accessible inline-SVG view button only for non-empty, non-legacy URLs; open it in a new tab.

## Phase 3: REFACTOR / Verification

- [x] 3.1 Refactor only after GREEN: reuse or clarify the existing blob-name/eligibility helpers without changing upload cleanup or delete behavior.
- [x] 3.2 Run `cd backend && pytest`; confirm all Azure operations remain mocked and deletion failures never block DB deletion.
- [x] 3.3 Run `cd frontend && npm test`; confirm eligible, legacy, and null URL scenarios pass with no API client change.

Threat matrix: all design rows are explicitly N/A; no additional threat RED tasks apply. No migration or `storage_service.py` change is required.
