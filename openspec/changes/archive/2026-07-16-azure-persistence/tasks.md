# Tasks: Azure Persistence

Reference shorthand: B = blob-storage spec; S = azure-sql spec; D-Arch, D-Flow, D-Files, D-Test, D-Contract, D-Consistency, D-Threat = matching design headings. Every pair is RED → GREEN → REFACTOR.

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 550–750 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 foundation; PR 2 Blob/upload; PR 3 migration/seed |
| Delivery strategy | ask-always |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Engine/config/GUID foundation | PR 1 | `cd backend && pytest tests/test_database.py tests/test_schemas.py` | SQLite + mocked MSSQL; no Azure | config, requirements, database, schemas |
| 2 | Blob persistence/upload | PR 2 | `cd backend && pytest tests/services/test_storage_service.py tests/api/test_invoices.py` | TestClient + mocked Azure | storage service, endpoint |
| 3 | Migration/engine-neutral seed | PR 3 | `cd backend && pytest tests/test_migrate_to_azure_sql.py tests/test_seed_db.py` | Temporary SQLite source/target | migration, seed |

## Phase 1: Foundation

- [x] 1.1 **RED** — Test `facturas-proveedores`, sole `DATABASE_URL`, and `azure-storage-blob`/`pymssql` declarations. (S: Environment-Selected; D-Files)
- [x] 1.2 **GREEN** — Update `backend/app/core/config.py`, `backend/.env`, `backend/requirements.txt`; no secrets; support SQLite and full `mssql+pymssql`. (S: Configuration; D-Arch)
- [x] 1.3 **RED** — Test SQLite options, MSSQL selection/session binding, and surfaced connection errors without fallback. (S: Environment-Selected/Failure Reporting; D-Test)
- [x] 1.4 **GREEN** — Update `backend/app/core/database.py` for configured URL, dialect-based SQLite args, and shared sessions. (D-Files/D-Flow)
- [x] 1.5 **RED** — Test GUID bind/result, MSSQL compilation, UUID IDs, and relationships. (S: GUID Compatibility; D-Contract)
- [x] 1.6 **GREEN** — Update `backend/app/models/schemas.py` `GUID` for MSSQL `UNIQUEIDENTIFIER` and UUID round trips. (S: GUID Compatibility; D-Contract)
- [x] 1.7 **REFACTOR** — Consolidate dialect fixtures and verify `cd backend && pytest tests/test_database.py tests/test_schemas.py`.

## Phase 2: Blob Storage

- [x] 2.1 **RED** — Mock Azure to test unique names, exact bytes/URL, missing config with no call, and controlled SDK failure. (B: Blob Service/Blob Naming; D-Test)
- [x] 2.2 **GREEN** — Create `backend/app/services/storage_service.py`: injectable client, validation, PDF content type, upload/delete, controlled exceptions. (D-Arch/D-Flow)
- [x] 2.3 **REFACTOR** — Remove SDK leakage from tests, document exception boundaries, and rerun the focused storage suite.

## Phase 3: Upload Integration

- [x] 3.1 **RED** — In `backend/tests/api/test_invoices.py`, mock extraction/storage; test original bytes, exact URL, `Pending`, 503, zero rows, rollback, and cleanup. (B: Upload Persistence/Failure; D-Flow)
- [x] 3.2 **GREEN** — Modify `backend/app/api/endpoints/invoices.py` to inject storage, upload after validation/UUID, persist URL only, rollback, map errors to 503. (D-Consistency)
- [x] 3.3 **REFACTOR** — Preserve existing duplicate/race-condition behavior and run `cd backend && pytest tests/api/test_invoices.py`.

## Phase 4: Migration and Seeding

- [x] 4.1 **RED** — With temporary SQLite, test seven tables, FK order `roles → users → suppliers → invoices → user_roles → line_items → audit_logs`, preserved IDs/relations, and mid-copy rollback. (S: Migration; D-Contract)
- [x] 4.2 **GREEN** — Create `backend/migrate_to_azure_sql.py`: source/target managers, `create_all`, one transaction, ordered inserts, failure reporting, no fallback. (D-Contract)
- [x] 4.3 **RED** — With temporary SQLite, test seed table creation, repeatability/no duplicates, relations, and atomic rollback. (S: Engine-Neutral Seed; D-Test)
- [x] 4.4 **GREEN** — Refactor `backend/seed_db.py` to configured `DatabaseManager`, all models, and idempotent atomic seeding. (D-Files)
- [x] 4.5 **REFACTOR/VERIFY** — Run `cd backend && pytest`; confirm D-Threat is N/A and no threat-matrix task is needed.
