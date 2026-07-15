# Tasks: Frontend Critical Pages — Integration Tests

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~430 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1: UploadInvoice → PR 2: ApprovalDashboard + Suppliers |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | UploadInvoice handlers + tests | PR 1 | base=main; ~140 lines; multipart + role + validation coverage |
| 2 | ApprovalDashboard + Suppliers handlers + tests + TESTING.md | PR 2 | base=main; ~190 lines; listing, approve/reject, search, role checks |

## Phase 1: UploadInvoice — Handlers & Tests

- [ ] 1.1 Create `UploadInvoice.handlers.ts` — MSW handler for `POST /api/invoices/upload` returning extracted invoice data
- [ ] 1.2 Write test: happy path → extraction review form replaces upload form after success
- [ ] 1.3 Write test: server 500 → `alert()` called, upload form preserved for retry
- [ ] 1.4 Write test: non-PDF file → validation error displayed, API never called
- [ ] 1.5 Write test: Viewer role → upload button disabled/not rendered

## Phase 2: ApprovalDashboard — Handlers & Tests

- [ ] 2.1 Create `ApprovalDashboard.handlers.ts` — MSW handlers for `GET /api/invoices` (list) and `PATCH /api/invoices/:id/approve`
- [ ] 2.2 Write test: loading state → "Loading invoices..." shown, then invoice rows + summary cards render
- [ ] 2.3 Write test: empty list → "No invoices found." in table body, summary cards show zero
- [ ] 2.4 Write test: Approve → `PATCH` called with `{ status: "Approved" }`, list refreshes
- [ ] 2.5 Write test: Reject → `PATCH` called with `{ status: "Rejected" }`, list refreshes

## Phase 3: Suppliers — Handlers & Tests

- [ ] 3.1 Create `Suppliers.handlers.ts` — MSW handlers for `GET /api/suppliers` and `POST /api/suppliers`
- [ ] 3.2 Write test: supplier list renders on mount with name, tax ID, email columns
- [ ] 3.3 Write test: Add Supplier button hidden for Viewer/Approver, visible for Admin
- [ ] 3.4 Write test: search input filters supplier rows dynamically by name/tax ID/email

## Phase 4: Final Verification & Documentation

- [ ] 4.1 Run `npm test` — all 11 new tests pass with no warnings
- [ ] 4.2 Create `TESTING.md` — document co-located page-test pattern with MSW handlers
- [ ] 4.3 Remove any temporary `console.log` / debug artifacts from test files
