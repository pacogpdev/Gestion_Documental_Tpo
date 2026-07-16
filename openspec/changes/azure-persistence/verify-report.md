schema: gentle-ai.verify-result/v1
evidence_revision: sha256:2b64b5156c376a97f142dadd7bba92a173c536eab1b2ad3832081c5693536dd4
verdict: pass
blockers: 0
critical_findings: 0
requirements: 9/9
scenarios: 9/13
test_command: cd backend && pytest --tb=short -v
test_exit_code: 0
test_output_hash: sha256:2b64b5156c376a97f142dadd7bba92a173c536eab1b2ad3832081c5693536dd4
build_command: cd backend && python -m compileall -q app migrate_to_azure_sql.py seed_db.py
build_exit_code: 0
build_output_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

# Verification Report: azure-persistence

## Executive Summary

The implementation conforms to the nine requirements and all 18 tasks are checked. The full backend suite passed: 52 tests passed, with no failures or skips. Runtime evidence is complete for the mocked Blob Storage and SQLite transaction paths; Azure SQL production behavior was not exercised against a reachable Azure resource, so four Azure-specific scenarios remain partial rather than fully runtime-proven.

## Mode and Completeness

- **Artifact store**: OpenSpec
- **Verification mode**: Strict TDD
- **Proposal artifact**: Not present in the change directory; proposal-to-implementation scope comparison was skipped.
- **Tasks total**: 18
- **Tasks complete**: 18
- **Tasks incomplete**: 0

## Build and Test Evidence

| Check | Result | Evidence |
|---|---|---|
| Full test suite | PASS | `cd backend && pytest --tb=short -v` — exit 0 |
| Test count | PASS | 52 passed, 0 failed, 0 skipped |
| Compilation | PASS | `cd backend && python -m compileall -q app migrate_to_azure_sql.py seed_db.py` — exit 0 |
| Focused persistence suite | PASS | 27 passed, 22 warnings |
| Migration CLI smoke test | PASS | Seven tables processed in declared order; exit 0 |
| Coverage | SKIPPED | No coverage plugin/tool detected in the project environment |
| Linter | SKIPPED | No linter configured or installed |
| Type checker | WARNING | `mypy` reported 20 errors across changed source and imported source files; see Quality Metrics |

### Test Results

```text
======================= 52 passed, 23 warnings in 2.21s =======================
```

Warnings are deprecations from Pydantic class-based configuration and `datetime.utcnow()` usage. They did not affect test execution.

## Spec Coverage

### Blob Storage — 4 requirements, 6 scenarios

| Requirement | Scenario | Covering test | Result |
|---|---|---|---|
| Azure Blob Storage Service | Successful mocked upload returns URL and sends bytes without network | `tests/services/test_storage_service.py::test_upload_pdf_sends_original_bytes_and_pdf_content_type_returns_blob_url` | ✅ COMPLIANT |
| Azure Blob Storage Service | Missing connection string does not call Azure | `tests/services/test_storage_service.py::test_missing_connection_string_raises_config_error_without_calling_azure` | ✅ COMPLIANT |
| Invoice Blob Naming | Supplier/invoice namespace, UUID uniqueness, `.pdf` suffix | `tests/services/test_storage_service.py::test_build_blob_name_uses_supplier_invoice_namespace_and_unique_pdf_names` | ✅ COMPLIANT |
| Invoice Upload Persistence | Exact blob URL persisted and invoice remains Pending | `tests/api/test_invoices.py::test_upload_persists_exact_blob_url_and_pending_status` | ✅ COMPLIANT |
| Invoice Upload Persistence | Original PDF bytes passed to storage | `tests/api/test_invoices.py::test_upload_persists_exact_blob_url_and_pending_status` | ✅ COMPLIANT |
| Storage Failure Consistency | Upload failure returns 503 and rolls back invoice/supplier rows | `tests/api/test_invoices.py::test_storage_failure_returns_503_and_rolls_back_invoice_and_supplier` | ✅ COMPLIANT |

**Blob scenario summary: 6/6 compliant.**

### Azure SQL — 5 requirements, 7 scenarios

| Requirement | Scenario | Covering test | Result |
|---|---|---|---|
| Environment-Selected Database Engine | SQLite manager uses SQLite options and supports local persistence | `tests/test_database.py::test_sqlite_engine_receives_check_same_thread_false`; `tests/test_seed_db.py::test_seed_creates_all_tables_and_fixture_data_on_configured_engine` | ✅ COMPLIANT |
| Environment-Selected Database Engine | `mssql+pymssql` URL is selected and bound to sessions | `tests/test_database.py::test_mssql_engine_uses_configured_url_without_sqlite_arguments` | ⚠️ PARTIAL — URL/session binding is verified with a mocked engine; no reachable Azure SQL connection was available |
| Azure SQL Configuration and Failure Reporting | Azure connection error propagates without SQLite fallback | `tests/test_database.py::test_connection_error_is_propagated_without_sqlite_fallback` | ✅ COMPLIANT |
| SQL Server GUID Compatibility | UUID IDs/FKs round-trip and MSSQL maps to `UNIQUEIDENTIFIER` | `tests/test_schemas.py::test_guid_uses_uniqueidentifier_for_mssql`; `test_guid_binds_mssql_values_as_canonical_strings`; `test_uuid_ids_and_foreign_keys_round_trip_on_sqlite` | ⚠️ PARTIAL — native MSSQL type/bind behavior and SQLite round trip pass, but no live SQL Server insert/read round trip was exercised |
| SQLite-to-Azure Migration | Seven tables, values, IDs, relationships, and FK order migrate | `tests/test_migrate_to_azure_sql.py::test_migrates_all_tables_preserving_values_and_relationships` | ⚠️ PARTIAL — complete transactional behavior is tested with SQLite source/target, not a live Azure SQL target |
| SQLite-to-Azure Migration | Mid-copy failure rolls back all copied rows | `tests/test_migrate_to_azure_sql.py::test_failed_copy_rolls_back_the_entire_target_transaction` | ⚠️ PARTIAL — rollback is runtime-proven on SQLite; Azure SQL rollback remains an unexercised deployment path |
| Engine-Neutral Seed Data | Tables/fixtures are created, second run is idempotent, relationships remain valid | `tests/test_seed_db.py::test_seed_creates_all_tables_and_fixture_data_on_configured_engine`; `test_seed_is_repeatable_without_duplicate_rows_or_relationships` | ⚠️ PARTIAL — both executions use SQLite; Azure SQL execution was not available |

**Azure SQL scenario summary: 3/7 compliant, 4/7 partial; no failing scenarios.**

**Overall scenario summary: 9/13 fully compliant, 4/13 partial, 0 failing.**

## Requirement Correctness

| Requirement | Status | Static implementation evidence |
|---|---|---|
| Azure Blob Storage Service | ✅ Implemented | `BlobStorageService` validates connection/container, injects `BlobServiceClient`, sets PDF content type, returns `blob_client.url`, and translates SDK failures. |
| Invoice Blob Naming | ✅ Implemented | `build_blob_name()` generates `{supplier_id}/{invoice_id}/{uuid}.pdf`. |
| Invoice Upload Persistence | ✅ Implemented | Upload route reads original bytes, uploads after validation/UUID assignment, persists only the returned blob URL, and uses `Pending`. |
| Storage Failure Consistency | ✅ Implemented | Controlled storage errors map to 503 and call `db.rollback()`; commit failures attempt best-effort blob cleanup. |
| Environment-Selected Database Engine | ✅ Implemented | `DatabaseManager` uses `DATABASE_URL` by default, applies SQLite-only options, and binds sessions to the selected engine. |
| Azure SQL Configuration and Failure Reporting | ✅ Implemented | `pymssql` is declared; credentials/endpoint are environment settings; engine errors are not caught or replaced with SQLite. |
| SQL Server GUID Compatibility | ✅ Implemented | `GUID.load_dialect_impl()` selects MSSQL `UNIQUEIDENTIFIER`; bind/result conversion preserves UUID values. |
| SQLite-to-Azure Migration | ✅ Implemented | `create_all()` precedes one target data transaction; rows copy in `roles → users → suppliers → invoices → user_roles → line_items → audit_logs` order. |
| Engine-Neutral Seed Data | ✅ Implemented | Seed uses the configured `DatabaseManager`, registers all models, creates missing schema, uses idempotent lookups, and commits fixture data atomically. |

## Design Coherence

| Design decision | Followed? | Evidence |
|---|---|---|
| Injectable `BlobServiceClient` wrapper | ✅ Yes | `BlobStorageService(..., client=...)` supports dependency injection and the route uses `get_storage_service`. |
| Upload before DB commit; rollback on storage failure | ✅ Yes | Blob upload occurs before invoice insertion/commit; storage failures rollback the pending session. |
| Best-effort blob deletion after DB failure | ✅ Yes | Commit and race failures call `_cleanup_uploaded_blob()`, which never masks the original error. |
| `DATABASE_URL` as sole engine selector | ✅ Yes | `DatabaseManager` reads `settings.DATABASE_URL` unless an explicit test override is supplied; no silent fallback exists. |
| GUID maps MSSQL to `UNIQUEIDENTIFIER` | ✅ Yes | `schemas.py` imports and returns SQLAlchemy MSSQL `UNIQUEIDENTIFIER`. |
| Migration in FK order | ✅ Yes | `TABLE_MIGRATION_ORDER` exactly matches the design contract. |

## Strict TDD Compliance

| Check | Result | Details |
|---|---|---|
| TDD evidence reported | ⚠️ Partial | Apply-progress artifacts contain TDD tables for PR 2 and PR 3, but no row-level TDD table for foundation tasks 1.1–1.7. |
| All tasks have tests | ✅ | All change-related test files exist and cover the foundation, Blob/upload, migration, and seed work units. |
| RED confirmed | ⚠️ Partial | RED/GREEN evidence is reported for PR 2 and PR 3 and all test files exist; the foundation RED chronology is not independently evidenced. |
| GREEN confirmed | ✅ | The current full run passes all 52 tests, including every change-related test. |
| Triangulation adequate | ✅ | Tests vary expected values and failure paths: names/bytes/errors, URL/status/rollback, UUID values/relationships, ordered copies, repeatability, and atomic failures. |
| Safety net | ⚠️ Partial | PR 2/3 apply evidence records safety-net runs; foundation safety-net evidence is not present in the available apply-progress artifact. |

**TDD evidence coverage: 11/18 tasks have explicit apply-progress table rows; 18/18 tasks are checked and their test files/behavior are present.**

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|---|---:|---:|---|
| Unit | 18 | 4 | pytest, unittest.mock |
| Integration | 21 | 3 | pytest, FastAPI TestClient, SQLite |
| E2E | 0 | 0 | Not used for this backend change |
| **Change-related total** | **39** | **7** | |

### Changed File Coverage

Coverage analysis skipped — no coverage tool detected in the project environment.

### Assertion Quality

✅ All reviewed assertions invoke production code and verify meaningful values or behavior. Empty-result assertions have companion non-empty tests; no tautologies, ghost loops, smoke-test-only cases, or assertion-free production paths were found.

### Quality Metrics

- **Linter**: ➖ Not available
- **Type checker**: ⚠️ `mypy` found 20 errors in 4 files, including the changed `database.py`, `schemas.py`, and `invoices.py`; these are informational quality findings and do not fail the runtime suite.

## Findings

### CRITICAL

None. No task is incomplete, no test failed, and no implementation-level spec violation was found.

### WARNING

1. Azure SQL scenarios are not runtime-tested against a reachable Azure SQL database. Native GUID round trip, production engine connection, migration target behavior, and seed repeatability on Azure SQL remain operational verification gaps.
2. Strict-TDD apply evidence is incomplete for foundation tasks 1.1–1.7: the available PR 2/3 artifacts do not provide the required row-level RED/GREEN/safety-net evidence for those tasks.
3. `mypy` reports 20 errors in changed/imported source files. Runtime tests pass, but the type-checking baseline is not clean.
4. The suite emits 23 deprecation warnings from Pydantic class-based configuration and `datetime.utcnow()`.
5. No proposal artifact was present, so proposal-to-implementation scope verification was skipped.

### SUGGESTION

1. Add an opt-in Azure SQL integration job with non-production credentials to prove native `UNIQUEIDENTIFIER` round trips, migration, and seed behavior on `mssql+pymssql`.
2. Add the missing foundation TDD Cycle Evidence rows to the apply-progress artifact, including RED, GREEN, triangulation, and safety-net evidence for tasks 1.1–1.7.
3. Resolve or explicitly baseline the `mypy` errors and migrate deprecated Pydantic/datetime usage in a follow-up cleanup change.

## Verdict

**PASS WITH WARNINGS** — implementation and all local tests pass; remaining warnings are limited to unexercised live Azure SQL behavior, incomplete foundation TDD provenance, type-checking errors, and deprecations.

## Next Recommended

`sdd-archive` is recommended. Before production rollout, execute the Azure SQL integration smoke tests and address the warnings above.
