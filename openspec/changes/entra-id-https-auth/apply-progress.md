# Apply Progress — Entra ID HTTPS Authentication and Authorization

**Change**: `entra-id-https-auth`
**Mode**: Strict TDD
**Delivery**: `auto-chain`; chain strategy `feature-branch-chain`; PR4 `feat/entra-id-https-auth-04-web` → `feat/entra-id-https-auth-03-api`; 400-line budget; current candidate accounting: +235/-157 = 392 changed lines against `feat/entra-id-https-auth-03-api`.

## Current Artifact State

- [x] 1.1 PR1: config, JWKS validation, and `AuthorizationPolicy` foundation complete.
- [x] 1.2 PR2: identity migration, synchronization, disable, and audit projection complete.
- [x] 1.3 PR3: endpoint matrix, sanitized `/users/me`, and public `/readyz` complete.
- [x] 1.4 PR4: MSAL core, route guards, navigation, and page action permission guards complete across the chained core and successor slices.
- [x] 1.5 PR5: secret-safe cert-manager issuer, production TLS ingress, and deferred redirect manifests complete by local rendered-manifest evidence only.
- [ ] Gate 0.2 remains unresolved: an SQL operator must authorize migration, backup, and restore before production application.
- [ ] Gate 0.3 remains unresolved: platform owners must provide cert-manager, DNS solver secret delivery, issuer inputs, DNS, and ingress support before any deployment.

## PR4 Web Authentication Core — 2026-09-03

**Boundary**: `feat/entra-id-https-auth-04-web` → `feat/entra-id-https-auth-03-api`; this is the safe core authentication slice. No product code, dependencies, tests, task checkbox, commit, push, PR, deployment, or migration changed in this evidence correction.

**Native attempt binding**: `pr4-web-authentication-core`, token `sha256:71bb7bdd3e59cc38b9353335a4429c4a0c64c2c6df09ca759c0b0043e2595739`; passing evidence remediates `sha256:4b784a66f13932b1f402a612ac7b2cc6570a3b46d0dab24f8d1629a387af2849`. No attempt lifecycle command was invoked.

### Strict TDD Core Evidence

| Work unit | Layer | Safety net | RED | GREEN | TRIANGULATE / REFACTOR |
|---|---|---|---|---|---|
| `pr4-test-harness` | Vitest/jsdom infrastructure | Initial focused command: exit 1, 2 files / 7 tests failed before test bodies (`localStorage` undefined). | N/A — no Task 1.4 behavior or test was added. | Same command: exit 0, 2 files / 7 tests passed. | N/A — deterministic harness correction only; minimal Map-backed `Storage` shim. |
| 1.4 PR4 core | Vitest unit/component | 2 files / 7 tests passed. | 4 new failures: missing session provider and guard. | 2 files / 5 tests passed. | Token/profile/401 and route-guard paths triangulated; refactor remained green. |

### Work Unit Evidence

- Core behavior: MSAL session acquisition, injectable bearer provider, server-derived `/users/me` profile, 401 clearing, protected routes, and permission-aware navigation are the complete PR4 scope.
- Focused command: `cd frontend && npx vitest run src/hooks/useAuth.test.ts src/routes/index.test.tsx` — exit 0, 2 files / 5 tests passed in 3.45s.
- Relevant frontend suite: `cd frontend && npx vitest run` — exit 0, 8 files / 51 tests passed in 5.08s; expected Node storage, React Router, and existing MSW warnings remained non-failing. Build: `cd frontend && npm run build` — exit 0; Vite built 880 modules in 4.41s with only the existing chunk-size warning.
- Runtime harness: Vitest/jsdom with mocked MSAL session and MSW `/users/me` exercises bearer attachment, profile load, 401 clearing, and denied-route behavior.
- Security inspection: no access token or profile is persisted by application code outside MSAL cache; legacy storage is removed and no sensitive logging exists in the scoped candidate.
- Deferred successor: page action `can(permission)` guards and their RED/GREEN tests remain intentionally deferred to the immediate successor chained PR. Task 1.4 remains unchecked until that successor completes.
- Git and cleanup: `git diff --check` passed; authoritative base accounting remains +235/-157 = 392 changed lines. Rollback is the PR4 frontend boundary `frontend/{package*,src/{api/client.ts,hooks/useAuth.ts,main.tsx,routes/index.tsx,components/Navbar.tsx,test-utils.tsx,hooks/useAuth.test.ts,routes/index.test.tsx}}`, retaining the test-only harness shim.

## PR4b Page Action Permissions — 2026-09-03

**Boundary**: `feat/entra-id-https-auth-04-actions` → `feat/entra-id-https-auth-04-web`; only Task 1.4's deferred page action guards and their behavior tests. Native binding: `pr4b-page-action-permissions`, token `sha256:2e60f47ecd3dbdb2cea477c3081fe89658d24893ba6cadeb04f9ff044f167c3c`; no attempt lifecycle command was invoked.

### Strict TDD Evidence

| Task | Test files | Layer | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 1.4 page actions | `ApprovalDashboard`, `UploadInvoice`, `Suppliers`, `SupplierDashboard` tests | Vitest component | 4 files / 43 tests passed | 7 failures / 43 passes: missing permission-based approval, delete, upload, statistics, supplier-admin, and dashboard guards | 4 files / 49 tests passed | Explicit permission-bearing Viewer interaction plus permission-absent Admin visibility prove permissions, not roles | Existing stale Viewer statistics expectations aligned with the approved server permission contract; focused suite remained green. |

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command | `cd frontend && npx vitest run src/pages/ApprovalDashboard.test.tsx src/pages/UploadInvoice.test.tsx src/pages/Suppliers.test.tsx src/pages/SupplierDashboard.test.tsx` — exit 0, 4 files / 49 tests passed in 3.96s. |
| Runtime harness | Vitest/jsdom with AuthProvider permission injection, MSW, React Query, and MemoryRouter exercised permission-based action visibility plus approved invoice PATCH and Viewer statistics navigation. |
| Full frontend suite | `cd frontend && npx vitest run` — exit 0, 8 files / 57 tests passed in 5.33s. |
| Build | `cd frontend && npm run build` — exit 0, 880 modules transformed in 6.49s; existing chunk-size warning only. |
| Rollback boundary | Revert `frontend/src/pages/{ApprovalDashboard,UploadInvoice,Suppliers,SupplierDashboard}.{tsx,test.tsx}` and this Task 1.4 record; this removes only PR4b page action guards. |

- Every prior direct page `hasRole` check is now `can(permission)`: invoice approve/reject uses `approve`; invoice delete uses `delete`; upload uses `upload`; supplier statistics and dashboard use `statistics`; supplier create/edit/delete uses `supplier_admin`.
- The UI remains a usability guard only; API authorization remains authoritative. No token/profile persistence or sensitive logging was introduced, and PR4 loading, unauthenticated, 401, and 403 behavior was untouched.
- Task 1.4 is complete because the PR4 core already covered session, login/logout, 401, protected routes, and navigation; this successor closes its remaining page action permission requirements. Final accounting against `feat/entra-id-https-auth-04-web` is +152/-34 = 186 changed lines. TLS, rollout, Task 1.5, and later work remain out of scope.

## PR4b Task 1.4 Critical Remediation — 2026-09-03

**Boundary**: `feat/entra-id-https-auth-04-actions` → `feat/entra-id-https-auth-04-web`; only the three failed Task 1.4 findings. Native binding: `pr4b-task14-critical-remediation`, token `sha256:77eda93ea4fa71f9331ff7415bb63e4582d581c10b753ee997c6dcfe25060ee6`; maximum two attempts and 186 additional changed lines. No `gentle-ai sdd-attempt` command was invoked. This evidence remediates the parent-settlement target `sha256:d272642325472869f7db0c73228e6f9403c4246b37baf421bbf3ca31b48f1b08` and does not change the independent verify report verdict.

### Strict TDD Evidence

| Finding | Safety net | RED | GREEN / Triangulation / Refactor |
|---|---|---|---|
| MSAL initialization | 6 files / 54 tests passed | `src/main.test.tsx` failed: `initialize` was not called. | Production-adapter deferred and already-resolved initialization cases passed; React rendering starts only after initialization resolves. |
| Bearer-safe page errors | Same green baseline | Upload 500 test failed because `console.error` received an Axios error. | 500 and 409 bearer-carrying failures pass with no console error; all four page raw Axios logging calls were removed. |
| Direct authenticated 403 | Same green baseline | Missing 403 handler, missing access-denied state, and missing alert test each failed. | Axios/MSW, AuthProvider, and route alert tests pass: 403 shows access denied and preserves the authenticated session, while 401 remains distinct. |

### Work Unit Evidence

- Focused GREEN/refactor: `cd frontend && npx vitest run src/main.test.tsx src/api/client.test.ts src/hooks/useAuth.test.ts src/routes/index.test.tsx src/pages/UploadInvoice.test.tsx` — exit 0, 5 files / 21 tests passed in 3.65s.
- Runtime harness: deferred production-MSAl adapter mock plus MSW Axios 403/500/409 responses, AuthProvider, and route notice directly exercised initialization ordering, bearer-safe failures, session-preserving 403, and visible denial UX.
- Full frontend suite: `cd frontend && npx vitest run` — exit 0, 9 files / 64 tests passed in 6.24s. Build: `cd frontend && npm run build` — exit 0, 880 modules transformed in 6.75s; only the existing chunk-size warning remains.
- Cleanup: page source has no `console.error`, `console.warn`, or `console.log`; application code still persists neither raw tokens nor profile data outside MSAL cache. No TLS, rollout, Task 1.5+, migration, commit, push, PR, or deployment action occurred.
- Git: `git diff --check` passed; authoritative `git diff --numstat feat/entra-id-https-auth-04-web` is +280/-53 = 333 changed lines, below the 400-line limit and 119 lines above the reported 214-line pre-remediation diff.
- Rollback boundary: revert `frontend/src/{main.tsx,api/client.ts,hooks/useAuth.ts,routes/index.tsx,pages/{ApprovalDashboard,UploadInvoice,Suppliers}.tsx,main.test.tsx,api/client.test.ts,hooks/useAuth.test.ts,routes/index.test.tsx,pages/UploadInvoice.test.tsx}` and this remediation record; it removes only this correction.

## PR5 TLS and cert-manager Manifests — 2026-09-03

**Boundary**: `feat/entra-id-https-auth-05-tls` → `feat/entra-id-https-auth-04-actions`; only Task 1.5's secret hygiene, cert-manager issuer, production TLS ingress, and deferred redirect. Native binding: `pr5-tls-manifests`, token `sha256:7eaabe4191248b4f897bd8a2240b987e6297cded5956bc0cfe6a58f7e26dc622`; no attempt lifecycle command was invoked.

### Strict TDD Evidence

| Task | Test file | Layer | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 1.5 | `backend/tests/test_k8s_manifests.py` | Rendered-manifest pytest | No existing manifest test existed: `pytest tests/test_k8s_manifests.py -q` exited 4 (`file or directory not found`) before the new test was written. | 3 failed in 0.50s: `ClusterIssuer` and explicit redirect deferral were absent. | 3 passed in 0.11s after the minimum manifest changes. | 4 passed in 0.14s after adding the base HTTP-only case. | 4 passed in 0.14s after extracting the production-render helper. |

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command | `cd backend && pytest tests/test_k8s_manifests.py -q` — exit 0, 4 passed in 0.12s. |
| Runtime harness | Test-local deterministic PyYAML renderer recursively loads the repository Kustomizations and merges their declared target patches; it exercised secret references, issuer/TLS wiring, hostname/routing consistency, and redirect deferral without a cluster or network call. |
| Renderer | `kubectl kustomize k8s/overlays/prod` is unavailable because `kubectl` is not on `PATH`; no alternative cluster tool or deployment was attempted. |
| Relevant regression | `cd backend && pytest tests/unit/test_auth_config.py -q` — exit 0, 4 passed in 0.03s. |
| Rollback boundary | Revert `backend/tests/test_k8s_manifests.py`, `backend/requirements.txt`, `k8s/base/{configmap.yaml,kustomization.yaml,secret.yaml}`, `k8s/overlays/prod/{configmap-patch.yaml,cluster-issuer.yaml,ingress-tls-patch.yaml,kustomization.yaml}`, the Task 1.5 checkbox/parent reference, and this PR5 record. |

- `backend-secrets` and `cert-manager-azuredns` are references only; no Secret, credentials, certificate, DNS token, tenant secret, or realistic secret value is rendered or created. An absent external secret prevents the affected workload or DNS solver from becoming ready.
- The base HTTP routes remain `/api` and `/health` to `backend:8000` and `/` to `frontend:80`. Production adds `facturas-tls` through ingress-shim with `nginx.ingress.kubernetes.io/ssl-redirect: "false"`; Task 1.6 alone may change that after `Certificate Ready=True` and an HTTPS probe/pilot.
- Gate 0.2 and Gate 0.3 remain closed. This work performed no database migration, cluster mutation, deployment, DNS change, certificate request, real secret creation, redirect enablement, commit, push, or PR action. The Task 1.4-scoped `verify-report.md` is unchanged; whole-change verification remains premature.
- Git cleanup: `git diff --check` passed; inclusive accounting against `feat/entra-id-https-auth-04-actions` is +194/-20 = 214 changed lines, including the three untracked test/manifest files.

## PR3 Endpoint Matrix Execution — 2026-09-02

**Boundary**: `feat/entra-id-https-auth-03-api` → `feat/entra-id-https-auth-02-identity`; task 1.3 only. The current correction is +114/-7 = 121 changed lines against `7a8783a`; the native behavior settlement was +115/-5 = 120 changed lines before evidence compaction; current total PR3 accounting is +321/-32 = 353 changed lines against `feat/entra-id-https-auth-02-identity`. PR #9 is open. Gate 0.2 remains unresolved; no production migration, deployment, or task 1.4 work occurred.

### Authorized Baseline Prerequisite (Separate from Task 1.3)

- Initial safety net: `python -m pytest backend/tests/api/test_invoices.py backend/tests/api/test_supplier_stats.py backend/tests/api/test_suppliers.py -q` — exit 1, 36 passed and 1 failed because the real storage provider leaked into `test_list_invoices_works_without_configured_storage`.
- Authorized isolation correction: replaced the test-only override removal with `override_storage(None)` in `backend/tests/api/test_invoices.py`.
- Proof: the isolated test passed (1 passed in 0.21s), then the original API safety net passed (37 passed in 3.61s). This prerequisite is not task 1.3 functional behavior.

### TDD Cycle Evidence

| Task | Test file | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 1.3 | `backend/tests/api/test_authorization_matrix.py` | FastAPI TestClient integration | API safety net — 37 passed | 5 failed, 8 passed: Viewer stats, Clerk deletion, Approver supplier creation, `Me` permissions, and `/readyz` were missing/wrong | 13 passed in 1.23s | Read allows all roles; stats covers four roles; 401 and distinct 403 paths assert invoice/supplier no-operation | Extracted a shared policy instance; 13 passed in 1.17s |

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command | `python -m pytest backend/tests/api/test_authorization_matrix.py -q` — 13 passed in 1.17s. |
| Runtime harness | FastAPI TestClient uses the real endpoint dependency graph and SQLite session: 13 focused cases pass, including 401/403 no-operation assertions. |
| Relevant regressions | Earlier API and identity/policy runs passed 37 and 42 tests; final serial composite run passed 79 tests in 4.15s. |
| Rollback boundary | Revert `backend/app/api/dependencies.py`, the three endpoint modules, `backend/app/main.py`, the two updated API tests, the new authorization-matrix test, and this task record; retain the explicitly authorized storage-isolation correction only if its standalone test remains needed. |

### PR9 Review-Correction — 2026-09-02
- **Evidence**: REV-001 — production-mode FastAPI TestClient/SQLite synchronization, disabled identity 403, and denied no-op proof; REV-002 — sanitized allowed/disabled/denied outcome, reason, correlation ID, and local audit ID events with forbidden sensitive fields absent; TDD safety 13, RED 3, GREEN/REFACTOR 16; API safety 37; identity-sync/authorization 42; `git diff --check` passed; runtime harness — production-mode FastAPI TestClient with real SQLite identity/role projection; rollback boundary — `backend/app/api/dependencies.py`, `backend/app/services/identity_sync_service.py`, `backend/tests/api/test_authorization_matrix.py`, and correction evidence; routing — `apply` for pending task 1.4 only after targeted PR3 review/CI, while verify/archive remain premature.
### Final Correction TDD Evidence — 2026-09-02

| Task | RED | GREEN | REFACTOR |
|---|---|---|---|
| 1.2 correction | `test_identity_sync.py` — 2 failed, 11 passed: NULL downgrade rebuilt before rejecting and Azure index lookups were unscoped. | Same command — 13 passed. | No further source refactor; same command — 13 passed. |

- SQLite NULL preflight rejects before rebuild and preserves the current schema and NULL row.
- Azure SQL `sys.indexes` email/identity lookups use `OBJECT_ID(N'dbo.users')`; DDL-intent coverage asserts it.

## Historical Evidence (retained; not current state)

Prior failures and evidence remain below for auditability. The current task state is only the summary above.

### TDD Cycle Evidence

| Task | Test files | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 1.1 | `test_auth_config.py`, `test_auth_jwks.py`, `test_authorization.py` | Unit | Prior record: `pytest tests/test_config.py app/core/test_config.py -q`: 6 passed; no remediation source edit | **Differential RED reconstruction** against base `6055ae7` in isolated worktree: config `3 failed, 1 passed`; JWKS `3 failed, 3 passed`; policy collection error (`ModuleNotFoundError`). This proves missing mode/JWKS/policy behavior, but cannot reconstruct historical RED for distinct wrong-audience, issuer, signature, expiry/nbf, timeout, and TTL cases. | Candidate after the first remediation artifact edit: focused `18 passed in 0.06s`; full `104 passed in 4.42s`. The prior `17 passed, 1 failed` setup correction is not accepted as a coherent GREEN sequence. | Incomplete: current persisted tests do not contain distinct timeout/TTL or wrong-audience, issuer, signature, expiry/nbf cases. | No remediation refactor. The prior constant extraction is not accepted as complete Strict-TDD evidence because the preceding GREEN record required a test-setup correction. |

### Strict-TDD Test Summary

- **Total tests written in this remediation**: 0; no test chronology is reconstructed or claimed.
- **Candidate tests after the first artifact remediation**: focused 18 passed in 0.06s; full 104 passed in 4.42s.
- **Differential RED reconstruction**: base `6055ae7` produced 6 failures, 4 passes, and 1 collection error across the copied focused files.
- **Layers used**: Unit only; no integration or E2E test was added in this slice.
- **Approval tests / pure functions**: None — this remediation changes evidence artifacts only.

### Differential Reconstruction Commands

- `git worktree add --detach "C:\Users\Paco Gómez\Documents\PROYECTO_FACTURAS_PROVEEDORES-worktrees\entra-id-https-auth-baseline" 6055ae7442c3b604cdffb4202345f4bf4eb2d3c1`
- In the isolated worktree's `backend/`: `pytest tests/unit/test_auth_config.py -q` — exit 1, 3 failed and 1 passed.
- In the isolated worktree's `backend/`: `pytest tests/unit/test_auth_jwks.py -q` — exit 1, 3 failed and 3 passed.
- In the isolated worktree's `backend/`: `pytest tests/unit/test_authorization.py -q` — exit 2, 1 collection error: `ModuleNotFoundError: No module named 'backend.app.core.authorization'`.

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command | `cd backend && pytest tests/unit/test_auth_config.py tests/unit/test_auth_jwks.py tests/unit/test_authorization.py -q` — 18 passed in 0.06s |
| Runtime harness | N/A — PR1 has no endpoint wiring (scheduled for PR3), the spec forbids an E2E framework in the foundation slice, and an external Entra call is not a deterministic runtime harness. The mocked unit suite is not presented as a distinct runtime harness. |
| Full test command | `cd backend && pytest -v` — 104 passed in 4.42s |
| Rollback boundary | Revert exactly `backend/app/core/config.py`, `backend/app/core/security.py`, `backend/app/core/authorization.py`, `backend/tests/unit/test_auth_config.py`, `backend/tests/unit/test_auth_jwks.py`, and `backend/tests/unit/test_authorization.py`; this removes only PR1 auth-foundation behavior. |

### Remaining Tasks

- [ ] 1.2 PR2: identity migration, synchronization, disable, audit projection.
- [ ] 1.3 PR3: endpoint matrix, sanitized `/users/me`, readiness/events.
- [ ] 1.4 PR4: MSAL session, token provider, permission routes/UI.
- [ ] 1.5 PR5: secret hygiene and certificate issuance manifests.
- [ ] 1.6 PR6: redirect gate and pilot/rollback runbook.

---

### PR2 Identity Projection Execution — 2026-09-02

Task 1.2 implements only the autonomous identity-projection slice. No endpoint, UI, TLS, deployment, or production database operation was performed. External gate 0.2 remains required before an operator applies the versioned migration with an approved backup/restore plan.

### TDD Cycle Evidence

| Task | Test file | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 1.2 | `backend/tests/integration/test_identity_sync.py` | Integration (SQLite) | `python -m pytest backend/tests/test_schemas.py backend/tests/test_audit_service.py backend/tests/test_seed_db.py -q` — exit 0, 11 passed in 0.50s | Initial: `python -m pytest backend/tests/integration/test_identity_sync.py -q` — exit 2, 1 collection error in 0.46s: `IdentitySyncService` did not exist. Correction: same command — exit 1, 4 failed and 6 passed in 1.88s, proving SQL grammar/downgrade, legacy email, shared-email, and filtered-index gaps. | Correction GREEN: same command — exit 0, 10 passed in 0.71s. | First/repeat sync cover create/update; disabled/revocation cover deny/remove; migration runs twice; race forces a uniqueness failure and recovery; legacy email, Clerk linkage, shared email, filtered fresh schema, and downgrade exercise distinct paths. | No further refactor required; focused command — exit 0, 10 passed in 0.69s. |

### Strict-TDD Test Summary

- **Total tests written**: 10 integration cases.
- **Total tests passing**: 10 focused; 15 relevant backend regression tests.
- **Layers used**: Unit (0), Integration (10), E2E (0).
- **Approval tests**: None — task 1.2 adds new behavior.
- **Pure functions created**: None — synchronization is an atomic persistence boundary.

### Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command | `python -m pytest backend/tests/integration/test_identity_sync.py -q` — exit 0, 10 passed in 0.70s. |
| Runtime harness | Same command — exit 0, 10 passed in 0.70s; each case uses the real SQLite SQLAlchemy schema, relationship persistence, uniqueness constraint, and audit row. |
| Relevant backend regression | `python -m pytest backend/tests/test_schemas.py backend/tests/test_audit_service.py backend/tests/test_seed_db.py backend/tests/test_migrate_to_azure_sql.py -q` — exit 0, 15 passed in 0.82s. |
| Rollback boundary | Revert `backend/app/models/schemas.py`, `backend/app/services/audit_service.py`, `backend/app/services/identity_sync_service.py`, `backend/migrations/__init__.py`, `backend/migrations/v001_add_entra_identity.py`, and `backend/tests/integration/test_identity_sync.py`. Do not apply the migration without gate 0.2. |

### Cumulative Task State

- [x] 1.1 PR1: config, JWKS validation, and `AuthorizationPolicy` foundation — native objective reset complete with strict-TDD proof.
- [x] 1.2 PR2: identity migration, synchronization, disable, audit projection — strict-TDD evidence above.
- [ ] 1.3 PR3: endpoint matrix, sanitized `/users/me`, readiness/events.
- [ ] 1.4 PR4: MSAL session, token provider, permission routes/UI.
- [ ] 1.5 PR5: secret hygiene and certificate issuance manifests.
- [ ] 1.6 PR6: redirect gate and pilot/rollback runbook.

## Scope Notes

Identity persistence is implemented only for task 1.2; endpoint-wide policy wiring, MSAL, and TLS remain unimplemented. External Entra prerequisites remain deployment gates only; deterministic local fixtures were sufficient for this slice.

## Remediation Disposition

Task 1.1 remains complete through its authorized native reset. Its prior historical-evidence limitation does not reopen task 1.2 or later tasks.

---

### PR2 Size-Exception Correction — 2026-09-02

**Delivery strategy**: `exception-ok`. The maintainer approved `size:exception` because the autonomous PR2 migration/synchronization slice was already 371/400 lines and the two independently validated migration blockers require the migration plus real SQLite regression coverage in the same review unit. PR2 remains `feat/entra-id-https-auth-02-identity` → `feat/entra-id-https-auth-01-auth`; no task 1.3 work was started.

### TDD Cycle Evidence

| Task | Safety Net | RED | GREEN | TRIANGULATE / REFACTOR |
|---|---|---|---|---|
| 1.2 correction | `python -m pytest backend/tests/integration/test_identity_sync.py -q` — 10 passed in 0.67s | Same command — 2 failed, 10 passed in 1.47s: real legacy unique email rejected a distinct tenant/OID, and downgrade removed a pre-existing Clerk role/assignment | Same command — 12 passed in 0.71s | Legacy shared-email sync plus rollback refusal exercises two data states; pre-existing Clerk role/assignment exercises a distinct ownership state. Refactor: same command — 12 passed in 0.72s. |

### Proof and Rollback Contract

- **Legacy email**: a real SQLite legacy `users.email UNIQUE NOT NULL` schema upgrades, then persists two different tenant/OID identities with the same email; the test observes two rows. Azure SQL DDL drops matching single-column unique constraints and indexes through `sys.key_constraints`/`sys.indexes` before permitting nullable email.
- **Ownership**: `entra_identity_migration_state` records the exact Clerk role ID only when this migration creates it, plus legacy email nullability/uniqueness. Downgrade deletes role links and the role only by that recorded ID; a pre-existing Clerk role and assignment survive actual SQLite upgrade/downgrade. It restores legacy email semantics, but refuses rollback before destructive DDL when post-migration data cannot satisfy a restored unique/non-null contract.

### Work Unit Evidence

- Focused/runtime SQLite migration, identity sync, relationship, audit, and downgrade harness: `python -m pytest backend/tests/integration/test_identity_sync.py -q` — 12 passed in 0.72s.
- Relevant regression: `python -m pytest backend/tests/test_schemas.py backend/tests/test_audit_service.py backend/tests/test_seed_db.py backend/tests/test_migrate_to_azure_sql.py -q` — 15 passed in 0.87s.
- Broad serial backend with `AZURE_STORAGE_CONNECTION_STRING=""`: `python -m pytest backend/tests -q` — 140 passed in 5.64s.
- Rollback boundary: `backend/migrations/v001_add_entra_identity.py` and `backend/tests/integration/test_identity_sync.py`; reverting them removes only this correction. Gate 0.2 remains explicit: no production migration, backup, or restore is authorized.
- Review accounting: final PR2 working-tree diff is **+506/-9 = 515 changed lines**; this **144-line** correction remains within the authorized 150-line correction cap and requires the accepted `size:exception`.

### Cumulative Task State

- [x] 1.2 PR2 remains complete with this maintainer-authorized correction.
- [ ] 1.3 PR3 and all later tasks remain unstarted.

---

### Native Objective Reset Execution — 2026-09-01

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
