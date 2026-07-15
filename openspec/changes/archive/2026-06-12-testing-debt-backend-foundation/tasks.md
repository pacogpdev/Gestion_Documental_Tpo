# Tasks: testing-debt-backend-foundation

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 200-350 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Infrastructure & Smoke Tests | PR 1 | Fix Windows locking + baseline plumbing |
| 2 | AI Service Validation | PR 1 | Full coverage for `ai_service` |
| 3 | Audit Service Validation | PR 1 | Full coverage for `audit_service` |

## Phase 1: Foundation & Infrastructure

- [x] 1.1 Modify `backend/tests/conftest.py`: Add `test_manager.engine.dispose()` to `db_session` teardown to resolve Windows `PermissionError`.
- [x] 1.2 Create `backend/tests/test_smoke.py`: Implement baseline tests verifying DB connectivity, API health, and service availability.

## Phase 2: AI Service Validation

- [x] 2.1 Create `backend/tests/test_ai_service.py`: Implement "Happy path" test verifying Azure AI response parsing into internal structures.
- [x] 2.2 Create `backend/tests/test_ai_service.py`: Implement "Empty response" test verifying 422 Unprocessable Entity error when no documents are found.
- [x] 2.3 Create `backend/tests/test_ai_service.py`: Implement "Malformed response" test verifying graceful handling of missing optional fields with defaults.
- [x] 2.4 Create `backend/tests/test_ai_service.py`: Implement "SDK failure" test verifying 500 Internal Server Error on Azure AI SDK exceptions.

## Phase 3: Audit Service Validation

- [x] 3.1 Create `backend/tests/test_audit_service.py`: Implement persistence test verifying `log_action` correctly saves records to the database.
- [x] 3.2 Create `backend/tests/test_audit_service.py`: Implement error handling test verifying propagation of database commit exceptions.

## Phase 4: Final Verification & Cleanup

- [x] 4.1 Verify Windows Cleanup: Run the full test suite on Windows and confirm the temporary SQLite file is successfully removed.
- [x] 4.2 Final Integration Check: Execute `test_smoke.py` to ensure all components are wired correctly.
