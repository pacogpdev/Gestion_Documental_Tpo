# Design: Azure Persistence

## Technical Approach

Keep the existing FastAPI/SQLAlchemy boundaries: extraction remains a pure AI-service operation, `BlobStorageService` owns Azure Blob calls, and `DatabaseManager` owns engine/session selection. The upload route performs extraction, validation, blob upload, and one database commit; Azure failures roll back the pending database transaction. `DATABASE_URL` is the sole engine selector, with SQLite for development and `mssql+pymssql` for production.

## Architecture Decisions

| Decision | Choice | Alternatives / rationale |
|---|---|---|
| Blob client | Injectable `BlobServiceClient` wrapper using connection string and `ContentSettings(content_type="application/pdf")` | Direct SDK calls in the route would make CI and failure testing brittle. The wrapper isolates Azure and returns `blob_client.url`. |
| Cross-service consistency | Upload before DB commit; rollback DB on storage failure; best-effort blob deletion if commit fails | A distributed transaction is unavailable. This ordering guarantees no invoice with a missing/local URL; cleanup limits orphaned blobs. |
| Engine selection | Construct SQLAlchemy from configured `DATABASE_URL`; detect `engine.dialect.name` for SQLite options | No silent fallback: an Azure connection error must remain an Azure error. |
| Migration | Explicit table-level copy in FK order inside a target transaction | ORM bulk migration is simple, preserves UUIDs/values, and makes ordering and rollback observable. |

## Data Flow

```text
UploadFile -> extract_invoice_data -> resolve/validate supplier + duplicate
           -> assign invoice UUID -> BlobStorageService.upload_pdf
           -> Invoice.file_url + line items -> db.commit -> response (Pending)
```

`BlobStorageService` exposes `build_blob_name(supplier_id, invoice_id)`, `upload_pdf(pdf_bytes, supplier_id, invoice_id) -> str`, and `delete_blob(blob_name)`. It validates connection string/container before creating a client, uses `{supplier_id}/{invoice_id}/{uuid}.pdf`, and raises controlled configuration/upload exceptions. The route receives it through a small dependency factory so tests can replace it. Storage errors map to HTTP 503, call `db.rollback()`, and never commit a local path.

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/app/services/storage_service.py` | Create | Blob client wrapper, naming, upload/delete, controlled errors, injectable client. |
| `backend/app/api/endpoints/invoices.py` | Modify | Inject storage; upload original `content` after validation and assigned UUID; persist returned URL; rollback on storage/commit failure. |
| `backend/app/core/database.py` | Modify | Use configured URL, dialect-based SQLite `connect_args`, and unchanged session dependency for either engine. |
| `backend/app/models/schemas.py` | Modify | `GUID` maps `mssql` to `UNIQUEIDENTIFIER`; bind/result conversion preserves `uuid.UUID`. |
| `backend/app/core/config.py`, `backend/.env` | Modify | Keep `DATABASE_URL` as the only database selector (dev SQLite, production full Azure SQL URL); change the existing container default/value to `facturas-proveedores`; keep the connection string environment-injected. No account secret or new Blob setting is hardcoded. |
| `backend/migrate_to_azure_sql.py` | Create | Source/target managers, schema creation, ordered copy, transaction and failure exit. |
| `backend/seed_db.py` | Modify | Use configured manager instead of forced SQLite; import all models; retain idempotent atomic fixture seeding. |
| `backend/requirements.txt` | Modify | Add `azure-storage-blob` and `pymssql`. |

## Interfaces / Contracts

`GUID.load_dialect_impl`: PostgreSQL → existing UUID, MSSQL → `sqlalchemy.dialects.mssql.UNIQUEIDENTIFIER`, otherwise `CHAR(36)`. For MSSQL bind UUIDs as strings accepted by the native type; result values always become `uuid.UUID`.

Migration order is `roles, users, suppliers, invoices, user_roles, line_items, audit_logs`. `create_all` runs against the target first; row inserts run in one target transaction. Any insert or connection error rolls back the copy and reports failure; no SQLite fallback or “completed” success is emitted.

## Testing Strategy (strict TDD: write these RED tests first)

| Layer | What to test | Approach |
|---|---|---|
| Unit | Blob naming, successful bytes/URL, missing configuration, SDK failure | Mock `BlobServiceClient.from_connection_string` and blob client; assert no Azure call on invalid config. |
| Integration | Upload stores exact blob URL, original bytes, Pending status; storage failure returns 503 and leaves zero invoice rows | Existing temporary SQLite fixtures; patch extraction and storage dependency, assert rollback and no local URL. |
| Unit/integration | SQLite and MSSQL dialect selection, GUID bind/result, no fallback | Temporary SQLite engine; compile/use a mocked MSSQL dialect and assert `UNIQUEIDENTIFIER`. |
| Integration | Migration preserves all seven tables, IDs, relationships, and rolls back mid-copy | Temporary SQLite source and target; inject a failing target insert. |
| Integration | Seed creates tables, is repeatable, and rolls back on failure | Temporary SQLite; run twice, then exercise the same functions with a configured target manager. |

## Threat Matrix

N/A — no routing security boundary beyond the existing FastAPI route, and no shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary is introduced.

## Migration / Rollout

Deploy dependencies and configuration first. Run the migration against an empty Azure SQL database, verify row counts/relationships, then switch production `DATABASE_URL`; keep SQLite configuration for local development. Blob persistence is immediately required for new uploads; existing local URLs are not rewritten by this change.

## Open Questions

- [ ] Confirm the production secret-management mechanism and whether the Azure container is provisioned before deployment; the application will not create it implicitly.
