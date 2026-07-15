# Proposal: Testing Debt - Backend Foundation

## Intent

The backend testing environment is currently fragile on Windows due to file locking issues (`PermissionError`), and critical business services (`ai_service.py` and `audit_service.py`) lack automated verification. This change aims to stabilize the testing infrastructure and establish a baseline of confidence for the core backend logic.

## Scope

### In Scope
- Fix `PermissionError` in `backend/tests/conftest.py` by ensuring SQLAlchemy engines are disposed before file deletion.
- Implement unit tests for `ai_service.py` using mocks for the Azure AI Form Recognizer SDK.
- Implement unit tests for `audit_service.py` using a temporary SQLite database.
- Establish a 'Smoke Test' suite to verify DB health and basic service plumbing.

### Out of Scope
- Frontend tests or UI-related verification.
- End-to-end integration tests across the full stack.
- Performance or load testing of the backend services.
- Tests for other backend services not mentioned here.

## Capabilities

### New Capabilities
- `backend-test-infrastructure`: Standardized setup and teardown for backend tests, including OS-specific handle management.
- `ai-service-validation`: Automated verification of AI extraction logic, including success and failure modes.
- `audit-service-persistence`: Automated verification of the audit trail's reliability and persistence.

### Modified Capabilities
- None

## Approach

1. **Environment Stability**: Modify `backend/tests/conftest.py` to call `engine.dispose()` before attempting to remove the temporary SQLite file, resolving the Windows `PermissionError`.
2. **AI Service Testing**: Use `unittest.mock` to simulate Azure AI Form Recognizer responses. Scenarios will include:
    - Successful document extraction.
    - Empty/unsupported documents.
    - Malformed data returned by the API.
    - API timeouts/failures (5xx errors).
3. **Audit Service Testing**: Create a dedicated pytest fixture that provides a transient in-memory or file-based SQLite database to verify that audit logs are correctly written and retrieved.
4. **Smoke Baseline**: Create `backend/tests/test_smoke_backend.py` to perform a "shallow" check of the most critical paths (DB connection -> Service call -> Response).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/tests/conftest.py` | Modified | Added `engine.dispose()` to fix Windows locks |
| `backend/tests/` | New | Addition of `test_ai_service.py`, `test_audit_service.py`, and `test_smoke_backend.py` |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Mock Drift | Medium | Document the Azure AI SDK versions used; plan periodic manual verification against the real API |
| SQLite $\neq$ Production DB | Low | Focus tests on business logic rather than DB-specific engine features |

## Rollback Plan

Since this change is primarily additive (tests) and involves a non-destructive fix to the test runner, the rollback plan is a simple `git revert` of the commits associated with this change.

## Dependencies

- Azure AI Form Recognizer SDK (for mock signatures)
- Pytest

## Success Criteria

- [ ] `pytest` runs to completion on Windows without `PermissionError`.
- [ ] `ai_service.py` has unit tests covering all specified failure/success scenarios.
- [ ] `audit_service.py` has unit tests verifying data persistence.
- [ ] Smoke tests pass, confirming the basic plumbing is functional.

## Proposal question round

*These questions are meant to uncover potential gaps in the product/business requirements before moving to the spec phase:*

1. **Business Risk**: If a bug in `ai_service` slips through these tests and causes incorrect data extraction in production, what is the immediate operational cost (e.g., manual correction time, financial risk)?
2. **Product Outcome**: Beyond "tests passing", does a "healthy backend foundation" imply a certain level of CI speed or a specific developer experience (e.g., "any developer can run all tests in < 30s")?
3. **Edge Cases**: For `audit_service`, are there high-concurrency scenarios or specific volume thresholds that we should verify now, or is basic functional persistence sufficient for this slice?
4. **Scope Boundaries**: Are there other "fragile" backend areas (e.g., migrations or seed scripts) that should be part of this "foundation" work, or are they deferred to a later change?
