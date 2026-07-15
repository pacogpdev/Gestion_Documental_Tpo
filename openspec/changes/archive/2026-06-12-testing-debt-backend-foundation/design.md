# Design: testing-debt-backend-foundation

## Technical Approach

This change stabilizes the backend test infrastructure for Windows and adds comprehensive verification for the AI and Audit services. The primary focus is resolving file locking issues with SQLite and implementing a robust mocking strategy for the Azure AI SDK.

## Architecture Decisions

### Decision: SQLite Connection Disposal

**Choice**: Explicitly call `engine.dispose()` in the `db_session` fixture.
**Alternatives considered**: Using `:memory:` databases.
**Rationale**: `:memory:` databases cause concurrency issues with FastAPI's threadpool. A temporary file is necessary, but on Windows, SQLAlchemy holds file handles until the engine is disposed, leading to `PermissionError` during cleanup.

### Decision: AI SDK Mocking Strategy

**Choice**: Mock at the `get_ai_client` factory level using `unittest.mock.patch`.
**Alternatives considered**: Creating a fake Azure AI SDK implementation.
**Rationale**: The Azure SDK is complex; patching the factory allows precise control over the `DocumentAnalysisClient` and its nested poller/result objects without recreating the entire SDK surface.

### Decision: Audit Service Verification

**Choice**: Direct DB state verification.
**Alternatives considered**: Mocking the DB session.
**Rationale**: Since we have a fast SQLite `db_session` fixture, verifying actual persistence in the database provides higher confidence than mocking the repository layer.

## Data Flow

### AI Validation Flow
`test` $\rightarrow$ `extract_invoice_data()` $\rightarrow$ `get_ai_client()` (Mocked) $\rightarrow$ `DocumentAnalysisClient` (Mock) $\rightarrow$ `poller.result()` (Mock) $\rightarrow$ `Parsed Data`

### Audit Persistence Flow
`test` $\rightarrow$ `AuditService.log_action()` $\rightarrow$ `db.add()` $\rightarrow$ `db.commit()` $\rightarrow$ `db.query()` (Verification)

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/tests/conftest.py` | Modify | Add `test_manager.engine.dispose()` to `db_session` teardown. |
| `backend/tests/test_ai_service.py` | Create | Tests for AI extraction (Happy path, Empty, Malformed, Error). |
| `backend/tests/test_audit_service.py` | Create | Tests for audit logging and persistence failure handling. |
| `backend/tests/test_smoke.py` | Create | Baseline "plumbing" tests for DB, API, and services. |

## Interfaces / Contracts

### AI Mock Structure
The mock will simulate the following hierarchy:
```python
# Mock return for get_ai_client()
mock_client = MagicMock(spec=DocumentAnalysisClient)
mock_poller = MagicMock()
mock_result = MagicMock()

mock_client.begin_analyze_document.return_value = mock_poller
mock_poller.result.return_value = mock_result
# mock_result.documents = [document_mock]
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `ai_service` parsing | Mock Azure SDK responses $\rightarrow$ assert internal dict. |
| Unit | `audit_service` persistence | Call `log_action` $\rightarrow$ query DB for record. |
| Integration | `db_session` cleanup | Run multiple tests $\rightarrow$ verify `test_db.sqlite` is removed. |
| Smoke | System "Plumbing" | Execute `test_smoke.py` covering DB/API/AI/Audit paths. |

## Migration / Rollout

No migration required. These are test infrastructure changes.

## Open Questions

- [ ] Verify if any other fixtures in `conftest.py` use the engine without the manager.
- [ ] Confirm if the smoke test suite should be integrated into a CI pipeline (expected: yes).
