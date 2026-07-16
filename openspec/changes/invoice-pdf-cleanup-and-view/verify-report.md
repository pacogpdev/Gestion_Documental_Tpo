schema: gentle-ai.verify-result/v1
evidence_revision: sha256:d1d9257b03912dea040e46cd2a640666520843d1ec581d72399404caf7a670e6
verdict: pass
blockers: 0
critical_findings: 0
requirements: 3/3
scenarios: 8/8
test_command: cd backend && pytest
test_exit_code: 0
test_output_hash: sha256:c3974c5b8ecaa55ee2952400ec64dae0857be9227989a8eb44e2d2296f9439db
build_command: cd frontend && npm run build
build_exit_code: 0
build_output_hash: sha256:53d40f5b2a501457ee062b952294892ed9060bd0d53a32384446e1df82a9ca29

# Verification Report: invoice-pdf-cleanup-and-view

## Executive Summary

The implementation conforms to all 3 retrieved requirements and all 8 scenarios. All 11 tasks are checked, the strict-TDD apply evidence is present, and the full backend and frontend suites pass. Verification completes with warnings for existing deprecations, unavailable coverage/lint tooling, and a non-clean backend mypy baseline; none is a functional blocker.

## Mode and Completeness

- **Artifact store**: OpenSpec
- **Verification mode**: Strict TDD
- **Proposal artifact**: Not present in the change directory; proposal-to-implementation comparison was skipped.
- **Apply-progress artifact**: Retrieved from Engram observation `#136` (`sdd/invoice-pdf-cleanup-and-view/apply-progress`).
- **Tasks total**: 11
- **Tasks complete**: 11
- **Tasks incomplete**: 0

## Build and Test Evidence

| Check | Result | Evidence |
|---|---|---|
| Full backend suite | PASS | `cd backend && pytest` — exit 0, 58 passed, 0 failed, 0 skipped |
| Full frontend suite | PASS | `cd frontend && npm test -- --run` — exit 0, 31 passed, 0 failed, 0 skipped |
| Backend compilation | PASS | `cd backend && python -m compileall -q app` — exit 0 |
| Frontend production build | PASS | `cd frontend && npm run build` — exit 0 |
| Backend focused suite | PASS | `cd backend && pytest tests/api/test_invoices.py` — exit 0, 19 passed |
| Frontend focused suite | PASS | `cd frontend && npm test -- --run src/pages/ApprovalDashboard.test.tsx` — exit 0, 12 passed |
| Coverage | SKIPPED | No pytest-cov or frontend coverage provider detected |

### Exact output hashes

| Command | Exit | SHA-256 output hash |
|---|---:|---|
| `cd backend && pytest` | 0 | `sha256:c3974c5b8ecaa55ee2952400ec64dae0857be9227989a8eb44e2d2296f9439db` |
| `cd frontend && npm test -- --run` | 0 | `sha256:669a4a7c1b0042389f2696ccd411201201001812115843063464e059cb3b88b7` |
| `cd backend && python -m compileall -q app` | 0 | `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `cd frontend && npm run build` | 0 | `sha256:53d40f5b2a501457ee062b952294892ed9060bd0d53a32384446e1df82a9ca29` |

Backend emitted 28 warnings, primarily existing Pydantic, Starlette/httpx, and `datetime.utcnow()` deprecations. Frontend emitted existing React Router future-flag warnings and expected console output from error-path tests.

## Spec Compliance Matrix

### Blob cleanup on delete

| Requirement | Scenario | Covering test | Result |
|---|---|---|---|
| Storage Failure Consistency | Azure upload failure returns controlled 503 and commits no invoice | `backend/tests/api/test_invoices.py::test_storage_failure_returns_503_and_rolls_back_invoice_and_supplier` | ✅ COMPLIANT |
| Storage Failure Consistency | Azure blob is requested for deletion and invoice is removed | `backend/tests/api/test_invoices.py::test_delete_invoice_removes_azure_blob_before_database_row` | ✅ COMPLIANT |
| Storage Failure Consistency | Legacy `/uploads/` path skips Azure deletion and invoice is removed | `backend/tests/api/test_invoices.py::test_delete_invoice_skips_legacy_upload_path` | ✅ COMPLIANT |
| Storage Failure Consistency | Blob deletion failure does not block database deletion | `backend/tests/api/test_invoices.py::test_delete_invoice_continues_when_blob_cleanup_fails` | ✅ COMPLIANT |

### PDF viewer

| Requirement | Scenario | Covering test | Result |
|---|---|---|---|
| Invoice Response Includes File URL | Stored Azure URL is returned unchanged as `fileUrl` | `backend/tests/api/test_invoices.py::test_list_invoices_preserves_azure_file_url` | ✅ COMPLIANT |
| PDF View Icon in Invoice List | Eligible URL opens in a new tab | `frontend/src/pages/ApprovalDashboard.test.tsx::renders the view control only for Azure URLs and opens the PDF in a new tab` | ✅ COMPLIANT |
| PDF View Icon in Invoice List | Legacy and missing URLs have no view control | `frontend/src/pages/ApprovalDashboard.test.tsx::hides the view control for legacy and missing file URLs` | ✅ COMPLIANT |
| PDF View Icon in Invoice List | Only the eligible row has an enabled view control | Both PDF view tests above, using Azure, `/uploads/`, and `null` fixtures | ✅ COMPLIANT |

**Compliance summary**: 8/8 scenarios compliant.

The missing-value response contract is additionally verified by `backend/tests/api/test_invoices.py::test_invoice_response_serializes_missing_file_url_as_null`, which asserts both Python `None` and JSON `null` serialization.

## Requirement Correctness

| Requirement | Status | Static implementation evidence |
|---|---|---|
| Storage Failure Consistency | ✅ Implemented | Upload storage failures map to 503 with rollback; delete cleanup is guarded broadly and database deletion proceeds; `/uploads/` is skipped. |
| Invoice Response Includes File URL | ✅ Implemented | `InvoiceResponse.fileUrl` is optional and `GET /api/invoices` maps the persisted `file_url` value without transformation. |
| PDF View Icon in Invoice List | ✅ Implemented | `ApprovalDashboard` renders an accessible inline-SVG button only when `fileUrl` is truthy and not a legacy `/uploads/` path; it calls `window.open(url, '_blank')`. |

## Design Coherence

| Design decision | Followed? | Evidence |
|---|---|---|
| Derive container-relative blob name with URL parsing | ✅ Yes | `_blob_name_from_url()` uses `urlparse`, removes the leading slash, requires the configured `container_name/` prefix, slices the relative name, and excludes query strings. |
| Best-effort cleanup before DB mutation | ✅ Yes | DELETE captures the stored URL, invokes guarded cleanup before deleting line items/invoice, and commits regardless of `delete_blob` exceptions. |
| Injectable storage boundary | ✅ Yes | DELETE receives `get_storage_service` via FastAPI dependency injection; tests replace it with `MagicMock`. |
| Additive camelCase response field | ✅ Yes | `InvoiceResponse.fileUrl` is optional (`str | None = None`) and list serialization maps `inv.file_url`. |
| Conditional local inline-SVG action | ✅ Yes | The existing Actions cell contains a row-specific `data-testid`, title, aria label, and no third-party icon dependency. |

## Strict TDD Compliance

| Check | Result | Details |
|---|---|---|
| TDD evidence reported | ✅ | Apply-progress observation `#136` contains a TDD Cycle Evidence table. |
| All tasks have tests | ✅ | 11/11 task rows identify a test file or focused suite. |
| RED confirmed | ✅ | 8/8 implementation-task rows report RED evidence; refactor/verification rows are correctly marked N/A. All listed files exist. |
| GREEN confirmed | ✅ | Full and focused runtime suites pass; the reported test files are green now. |
| Triangulation adequate | ✅ | Evidence covers distinct success, legacy, failure, URL, null, and browser-tab behaviors. |
| Safety net for modified files | ✅ | Apply-progress records baseline or focused-suite safety-net evidence for all task rows. |

**TDD Compliance**: 6/6 applicable checks passed.

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|---|---:|---:|---|
| Unit | 0 | 0 | No standalone unit file for this change |
| Integration | 31 | 2 | pytest + FastAPI TestClient + SQLite + MagicMock; Vitest + React Testing Library + MSW |
| E2E | 0 | 0 | No browser E2E harness used |
| **Change-related total** | **31** | **2** | |

The backend file is API integration/model-contract coverage (19 tests); the frontend file is component integration coverage (12 tests). No live Azure or browser runtime was required by the design.

### Changed File Coverage

Coverage analysis skipped — no coverage tool/provider was detected.

### Assertion Quality

✅ All reviewed assertions invoke production code and verify meaningful values or behavior. The empty-list assertion has a companion populated-list test; no tautologies, ghost loops, assertion-free paths, smoke-test-only cases, or mock-heavy violations were found in the change-specific tests.

### Quality Metrics

- **Linter**: ➖ Not configured; no frontend lint script or backend linter was detected.
- **Backend type checker**: ⚠️ `mypy app` found 37 baseline errors; 18 are reported in changed `app/models/schemas.py` and `app/api/endpoints/invoices.py`, while the remaining errors are in unchanged files/imports.
- **Frontend type checker**: ⚠️ `npx tsc --noEmit` could not run as a project because no `tsconfig.json` exists. The production Vite build passed.

## Findings

### CRITICAL

None. No task is incomplete, no declared test/build command failed, and no spec scenario lacks a passing covering test.

### WARNING

1. The full suites emit existing deprecation/future-flag warnings: 28 backend warnings and React Router warnings in frontend tests.
2. Coverage is not available in the current environment, so changed-file line/branch coverage cannot be reported.
3. Backend mypy is not clean: 18 errors touch changed source files, although runtime tests and compilation pass.
4. A frontend project type-check command is not configured because `tsconfig.json` is absent; Vite production build remains green.

### SUGGESTION

1. Add an endpoint-level test that maps a database row with a missing `file_url` through `GET /api/invoices`, complementing the direct `InvoiceResponse` JSON-null test.
2. Consider an explicit delete-path test for storage dependency construction failure if the best-effort guarantee is intended to include unavailable Azure configuration, not only `delete_blob` failures.

## Verdict

**PASS WITH WARNINGS** — all requirements, scenarios, tasks, and runtime checks pass; remaining findings are tooling/baseline quality warnings and optional edge-case coverage improvements.

## Next Recommended

`sdd-archive` is recommended.
