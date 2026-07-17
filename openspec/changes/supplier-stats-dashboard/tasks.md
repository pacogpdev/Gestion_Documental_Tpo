# Tasks: Supplier Statistics Dashboard

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 400–600 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 backend API → PR 2 frontend dashboard |
| Delivery strategy | ask-on-risk (user selected ask-always) |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | API contract and aggregation | PR 1 | `cd backend && pytest tests/api/test_supplier_stats.py` | TestClient + SQLite seeded fixtures | `suppliers.py`, `schemas.py`, API test |
| 2 | Dashboard and navigation | PR 2 | `cd frontend && npm test -- SupplierDashboard Suppliers` | Vitest/MSW browser-like harness | dashboard, route, nav, dependency, UI tests |

## Phase 1: Backend RED Tests

- [x] 1.1 Create `backend/tests/api/test_supplier_stats.py`; seed relative-window/outside-window invoices, second supplier, statuses, repeated descriptions, and 11+ items; assert 12 ordered buckets/zero-fill, totals, average, grand total/percentage, status counts, top invoice, top-10 aggregation, and empty supplier.
- [x] 1.2 Add RED API scenarios for unknown supplier (404) and explicit Admin/Approver success versus Clerk/Viewer 403, enabling role enforcement through dependency overrides.

## Phase 2: Backend GREEN / Refactor

- [x] 2.1 Add camelCase `MonthlyAmount`, `TopLineItem`, `StatusDistribution`, `TopInvoice`, and `SupplierStatsResponse` models in `backend/app/models/schemas.py`; make RED contract tests pass.
- [x] 2.2 Add `GET /api/suppliers/{id}/stats` in `backend/app/api/endpoints/suppliers.py` with one trailing-12-month range, cross-dialect aggregates, zero-safe values, top-10 ordering, and `RoleChecker(["Admin", "Approver"])`; pass API RED tests.
- [x] 2.3 Refactor query/date helpers without changing the response contract; run `cd backend && pytest`.

## PR 1 Apply Evidence

### TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 1.1 | `backend/tests/api/test_supplier_stats.py` | Integration | ✅ 4/4 | ✅ Written first; initial route returned 404 | ✅ 11 passed | ✅ Window boundaries, zero-fill, totals, percentage, top items, statuses, and empty supplier | ✅ Focused suite remained 11 passed |
| 1.2 | `backend/tests/api/test_supplier_stats.py` | Integration | ✅ 4/4 | ✅ Written first; initial route returned 404/Not Found | ✅ 11 passed | ✅ Admin/Approver success plus Clerk/Viewer denial and unknown supplier | ✅ Focused suite remained 11 passed |
| 2.1 | `backend/tests/api/test_supplier_stats.py` | Integration | ✅ 4/4 | ✅ Contract tests preceded response models | ✅ 11 passed | ✅ Non-empty and zero-value response paths | ✅ Full suite remained green |
| 2.2 | `backend/tests/api/test_supplier_stats.py` | Integration | ✅ 4/4 | ✅ Contract tests preceded endpoint implementation | ✅ 11 passed | ✅ Cross-supplier totals, repeated descriptions, 12 buckets, and role matrix | ✅ Full suite remained green |
| 2.3 | `backend/tests/api/test_supplier_stats.py` | Integration | ✅ 11/11 | ✅ Existing contract tests captured behavior before refactor | ✅ 11 passed | ✅ Same contract exercised across populated and empty datasets | ✅ Extracted date/month/status helpers; 11 passed |

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `cd backend && pytest tests/api/test_supplier_stats.py -q` → **11 passed** |
| Runtime harness command/scenario and exact result | FastAPI `TestClient` with SQLite seeded fixtures → **11 integration scenarios passed** |
| Full test command and exact result | `cd backend && pytest` → **86 passed** (75 existing + 11 new) |
| Rollback boundary | Revert `backend/app/api/endpoints/suppliers.py`, `backend/app/models/schemas.py`, `backend/tests/api/test_supplier_stats.py`, and the PR 1 task evidence entries without touching frontend work |

## Phase 3: Frontend RED Tests

- [x] 3.1 Extend `frontend/src/pages/Suppliers.test.tsx` with RED tests for accessible stats links, supplier-specific destination, Admin/Approver visibility, and Clerk/Viewer exclusion.
- [x] 3.2 Create `frontend/src/pages/SupplierDashboard.handlers.ts` fixtures and `SupplierDashboard.test.tsx`; assert fetch, headings/KPIs, four chart labels, empty state, API error, unknown supplier, and Back navigation.
- [x] 3.3 Add route smoke coverage for `/suppliers/:id/dashboard` and RED Navbar coverage proving Approvers can reach Suppliers.

## Phase 4: Frontend GREEN / Integration

- [x] 4.1 Add `recharts` to `frontend/package.json` and lockfile; create `SupplierDashboard.tsx` with role gate, API loading/error states, KPI cards, responsive charts, empty states, labels, and test IDs.
- [x] 4.2 Modify `Suppliers.tsx` with keyboard-accessible chart actions; update `frontend/src/routes/index.tsx` and `frontend/src/components/Navbar.tsx` for the dashboard route and Approver access; pass all frontend RED tests.
- [x] 4.3 Refactor presentation/accessibility details and run `cd frontend && npm test` plus the production build.

## PR 2 Apply Evidence

### TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 3.1 | `frontend/src/pages/Suppliers.test.tsx` | Component | ✅ 9/9 | ✅ Written first; stats action absent | ✅ 15 passed | ✅ Admin/Approver visibility, Clerk/Viewer exclusion, accessible name, supplier-specific navigation | ✅ Keyboard-accessible button and role-gated action |
| 3.2 | `frontend/src/pages/SupplierDashboard.test.tsx` | Component/integration | N/A (new) | ✅ Written first; page module missing | ✅ 7 passed | ✅ Populated, empty, API 500, API 404, unauthorized, and actual backend field aliases | ✅ Extracted response normalization and stable role boolean dependency |
| 3.3 | `frontend/src/routes/index.test.tsx`, `frontend/src/components/Navbar.test.tsx` | Component/integration | N/A (new coverage) | ✅ Written first; route/link unavailable | ✅ 2 passed | ✅ Dashboard route smoke and Approver Suppliers access | ✅ Accessible navigation remains green |
| 4.1 | `frontend/src/pages/SupplierDashboard.test.tsx` | Component/integration | N/A (new) | ✅ Contract tests preceded page implementation | ✅ 7 passed | ✅ Four chart regions, KPI values, zero data, and error paths | ✅ Responsive chart cards and reusable KPI/empty components |
| 4.2 | `frontend/src/pages/Suppliers.test.tsx`, `frontend/src/routes/index.test.tsx`, `frontend/src/components/Navbar.test.tsx` | Component/integration | ✅ 9/9 Suppliers tests | ✅ Navigation/role tests preceded implementation | ✅ 17 focused tests passed | ✅ Admin/Approver/Clerk/Viewer matrix and route navigation | ✅ Reused existing icon styling and role patterns |
| 4.3 | All frontend tests | Component/integration | ✅ 34/34 existing tests | ✅ New behavior tests were red before implementation | ✅ 49 passed | ✅ Full suite plus production build | ✅ Normalized API contract, added labels/test IDs, preserved existing behavior |

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `cd frontend && npx vitest run src/pages/Suppliers.test.tsx src/pages/SupplierDashboard.test.tsx src/components/Navbar.test.tsx src/routes/index.test.tsx` → **4 files, 24 tests passed** |
| Runtime harness command/scenario and exact result | React Testing Library + MSW browser-like harness → **24 focused integration/component scenarios passed**, including API loading/error, role gates, chart labels, and navigation |
| Full test command and exact result | `cd frontend && npx vitest run` → **8 files, 49 tests passed** (34 existing + 15 new) |
| Production build | `cd frontend && npm run build` → **success**; Vite emitted a chunk-size warning for the Recharts bundle |
| Rollback boundary | Revert `frontend/src/pages/SupplierDashboard.tsx`, `frontend/src/pages/Suppliers.tsx`, `frontend/src/routes/index.tsx`, `frontend/src/components/Navbar.tsx`, the four co-located frontend test/fixture files, and the Recharts package/lockfile entries without touching PR 1 backend files |
