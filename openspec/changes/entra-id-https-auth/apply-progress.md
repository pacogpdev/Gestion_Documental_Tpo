# Apply Progress — Entra ID HTTPS Authentication and Authorization

**Change**: `entra-id-https-auth`
**Mode**: Strict TDD
**Delivery**: Chained PR slice #1 (`feat/entra-id-https-auth-01-auth` → `feat/entra-id-https-auth`)

## Reopened Tasks

- [ ] 1.1 PR1: config, JWKS validation, and `AuthorizationPolicy` foundation. Reopened because the original record cannot prove the required Strict-TDD sequence.

## TDD Cycle Evidence

| Task | Test files | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 1.1 | `test_auth_config.py`, `test_auth_jwks.py`, `test_authorization.py` | Unit | Prior record: `pytest tests/test_config.py app/core/test_config.py -q`: 6 passed; no remediation source edit | **Differential RED reconstruction** against base `6055ae7` in isolated worktree: config `3 failed, 1 passed`; JWKS `3 failed, 3 passed`; policy collection error (`ModuleNotFoundError`). This proves missing mode/JWKS/policy behavior, but cannot reconstruct historical RED for distinct wrong-audience, issuer, signature, expiry/nbf, timeout, and TTL cases. | Candidate after the first remediation artifact edit: focused `18 passed in 0.06s`; full `104 passed in 4.42s`. The prior `17 passed, 1 failed` setup correction is not accepted as a coherent GREEN sequence. | Incomplete: current persisted tests do not contain distinct timeout/TTL or wrong-audience, issuer, signature, expiry/nbf cases. | No remediation refactor. The prior constant extraction is not accepted as complete Strict-TDD evidence because the preceding GREEN record required a test-setup correction. |

## Strict-TDD Test Summary

- **Total tests written in this remediation**: 0; no test chronology is reconstructed or claimed.
- **Candidate tests after the first artifact remediation**: focused 18 passed in 0.06s; full 104 passed in 4.42s.
- **Differential RED reconstruction**: base `6055ae7` produced 6 failures, 4 passes, and 1 collection error across the copied focused files.
- **Layers used**: Unit only; no integration or E2E test was added in this slice.
- **Approval tests / pure functions**: None — this remediation changes evidence artifacts only.

## Differential Reconstruction Commands

- `git worktree add --detach "C:\Users\Paco Gómez\Documents\PROYECTO_FACTURAS_PROVEEDORES-worktrees\entra-id-https-auth-baseline" 6055ae7442c3b604cdffb4202345f4bf4eb2d3c1`
- In the isolated worktree's `backend/`: `pytest tests/unit/test_auth_config.py -q` — exit 1, 3 failed and 1 passed.
- In the isolated worktree's `backend/`: `pytest tests/unit/test_auth_jwks.py -q` — exit 1, 3 failed and 3 passed.
- In the isolated worktree's `backend/`: `pytest tests/unit/test_authorization.py -q` — exit 2, 1 collection error: `ModuleNotFoundError: No module named 'backend.app.core.authorization'`.

## Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command | `cd backend && pytest tests/unit/test_auth_config.py tests/unit/test_auth_jwks.py tests/unit/test_authorization.py -q` — 18 passed in 0.06s |
| Runtime harness | N/A — PR1 has no endpoint wiring (scheduled for PR3), the spec forbids an E2E framework in the foundation slice, and an external Entra call is not a deterministic runtime harness. The mocked unit suite is not presented as a distinct runtime harness. |
| Full test command | `cd backend && pytest -v` — 104 passed in 4.42s |
| Rollback boundary | Revert exactly `backend/app/core/config.py`, `backend/app/core/security.py`, `backend/app/core/authorization.py`, `backend/tests/unit/test_auth_config.py`, `backend/tests/unit/test_auth_jwks.py`, and `backend/tests/unit/test_authorization.py`; this removes only PR1 auth-foundation behavior. |

## Remaining Tasks

- [ ] 1.2 PR2: identity migration, synchronization, disable, audit projection.
- [ ] 1.3 PR3: endpoint matrix, sanitized `/users/me`, readiness/events.
- [ ] 1.4 PR4: MSAL session, token provider, permission routes/UI.
- [ ] 1.5 PR5: secret hygiene and certificate issuance manifests.
- [ ] 1.6 PR6: redirect gate and pilot/rollback runbook.

## Scope Notes

No identity persistence, endpoint-wide policy wiring, MSAL, or TLS behavior was implemented. External Entra prerequisites remain deployment gates only; deterministic local fixtures were sufficient for this slice.

## Remediation Disposition

Task 1.1 remains incomplete. The isolated baseline proves several differential failures without mutating the candidate, but the missing per-case historical RED evidence and incoherent setup-correction sequence cannot be repaired retroactively without inventing chronology.

---

## Native Objective Reset Execution — 2026-09-01

The maintainer authorized a native reset bound to failed evidence `sha256:d6b7ac52eb1c12d220ac0fc1270d589ba03fc208081d85523a71e8d163000c42`. No settlement action was performed here.

### Reset Confirmation

- Restored `backend/app/core/config.py` and `backend/app/core/security.py` to `HEAD` and removed the four candidate-created files in the rollback boundary before writing implementation.
- Boundary check reported `TRACKED_BOUNDARY_CLEAN=True`; `authorization.py` and all three focused test files were absent. Therefore the candidate could no longer match the previously failed implementation state.
- Existing-file safety net: `pytest tests/test_config.py app/core/test_config.py tests/api/test_supplier_stats.py -q` — `17 passed in 1.15s`.

### TDD Cycle Evidence

| Behavior group | RED — tests written first and exact result | Minimal GREEN — exact result | REFACTOR — exact result |
|---|---|---|---|
| Explicit local bypass and fail-closed configuration | `pytest tests/unit/test_auth_config.py -q` — `4 failed in 0.42s`: no `is_local_development` property and invalid local-dev/production and missing-Entra configurations did not raise. An earlier `2 failed, 2 passed in 0.37s` probe was corrected before production code because its direct constructor inputs were rejected as extras rather than exercising environment configuration. | `pytest tests/unit/test_auth_config.py -q` — `4 passed in 0.03s`. | Extracted `ENTRA_REQUIRED_FIELDS`; `pytest tests/unit/test_auth_config.py -q` — `4 passed in 0.03s`. |
| Valid API access token; wrong audience; wrong issuer; bad signature; expired; not-before | `pytest tests/unit/test_auth_jwks.py -q -k "valid_access_token or invalid_claims or bad_signature"` — `6 failed, 3 deselected in 0.68s`: valid v2 API token could not validate and every rejection leaked provider details instead of the safe 401 response. | `pytest tests/unit/test_auth_jwks.py -q -k "valid_access_token or invalid_claims or bad_signature"` — `6 passed, 3 deselected in 0.25s`. | Extracted `_has_scope`; `pytest tests/unit/test_auth_jwks.py -q -k "valid_access_token or invalid_claims or bad_signature"` — `6 passed, 3 deselected in 0.42s`. |
| JWKS timeout/outage safe 503; TTL caching; one refresh on unknown `kid` | `pytest tests/unit/test_auth_jwks.py -q -k "timeout or cache_refreshes or unknown_kid"` — `3 failed, 6 deselected in 0.50s`: timeout was 401, TTL support was absent, and unknown `kid` did not refresh. The cache-clock test setup was corrected before GREEN and rerun RED: `3 failed, 6 deselected in 0.45s`. | `pytest tests/unit/test_auth_jwks.py -q -k "timeout or cache_refreshes or unknown_kid"` — `3 passed, 6 deselected in 0.16s`. | Extracted `_find_key`; `pytest tests/unit/test_auth_jwks.py -q -k "timeout or cache_refreshes or unknown_kid"` — `3 passed, 6 deselected in 0.29s`. |
| Approved `AuthorizationPolicy` matrix | `pytest tests/unit/test_authorization.py -q` — exit 2, collection error `ModuleNotFoundError: No module named 'backend.app.core.authorization'`. | `pytest tests/unit/test_authorization.py -q` — `29 passed in 0.06s`. | Extracted `ROLE_OPERATIONS`; `pytest tests/unit/test_authorization.py -q` — `29 passed in 0.06s`. |

The security source was restored to `HEAD` after an early combined security change was identified as prematurely including the untested JWKS-resilience behavior. The accepted token and JWKS cycles above were then rerun from that clean security boundary; this record preserves that correction rather than claiming a fabricated chronology.

### Strict-TDD Test Summary

- **Total tests written**: 42 unit-test cases across config (4), JWT/JWKS (9), and policy matrix (29).
- **Total tests passing**: 42 focused; 128 full backend suite.
- **Layers used**: Unit (42), Integration (0), E2E (0).
- **Approval tests**: None — this was new behavior, not a behavior-preserving refactor.
- **Pure functions created**: 2 (`_has_scope`, `_find_key`).
- **Regression correction**: the first full run found three pre-existing API role tests incompatible with the explicit-mode change because `RoleChecker` still bypassed roles in local mode. Removing that redundant bypass restored `pytest tests/api/test_supplier_stats.py tests/api/test_suppliers.py -q` to `15 passed in 1.52s`; the `DEV_USER` remains an Admin through `get_current_user` in explicit local-dev mode.

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused command | `cd backend && pytest tests/unit/test_auth_config.py tests/unit/test_auth_jwks.py tests/unit/test_authorization.py -q` — `42 passed in 0.52s`. |
| Full command | `cd backend && pytest -v` — `128 passed in 4.86s`. |
| Runtime harness | N/A — slice #1 has no endpoint wiring (scheduled for slice #3), introduces no deterministic external Entra boundary, and the foundation must not add an E2E framework. The mocked unit suite is not represented as a separate runtime harness. |
| Authored line count | 370 additions plus deletions across the six implementation/test files; 137 are production-source additions/deletions. Both are within the 400-line slice budget. |
| Exact rollback boundary | `backend/app/core/config.py`, `backend/app/core/security.py`, `backend/app/core/authorization.py`, `backend/tests/unit/test_auth_config.py`, `backend/tests/unit/test_auth_jwks.py`, `backend/tests/unit/test_authorization.py`. Reverting only these files removes the PR1 auth foundation without touching slice #2 or SDD artifacts. |

### Cumulative Task State

- [x] 1.1 PR1: config, JWKS validation, and `AuthorizationPolicy` foundation — native objective reset complete with strict-TDD proof.
- [ ] 1.2 PR2: identity migration, synchronization, disable, audit projection.
- [ ] 1.3 PR3: endpoint matrix, sanitized `/users/me`, readiness/events.
- [ ] 1.4 PR4: MSAL session, token provider, permission routes/UI.
- [ ] 1.5 PR5: secret hygiene and certificate issuance manifests.
- [ ] 1.6 PR6: redirect gate and pilot/rollback runbook.
