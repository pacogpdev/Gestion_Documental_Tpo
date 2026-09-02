# Tasks: Entra ID HTTPS Authentication and Authorization

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 1,400–2,000 total; each slice <=400 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Delivery strategy / chain | auto-chain / feature-branch-chain |
| Suggested split | Auth → identity → API → web → TLS → rollout |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

## Chain and Work Units

Tracker: draft/no-merge `feat/entra-id-https-auth` from `main`, with its tracker PR targeting `main`. Review children in order; after approval integrate bottom-up (PR6 → PR5 → PR4 → PR3 → PR2 → PR1 → tracker), then merge the tracker. Every PR body includes Chain Context and a diagram marking its own position with `📍`; retarget/rebase any polluted child diff.

| PR / branch / exact base | Scope and strict TDD | Evidence / runtime / rollback |
|---|---|---|
| #1 `feat/entra-id-https-auth-01-auth` → tracker | RED, GREEN, REFACTOR config/JWKS/`AuthorizationPolicy`; first autonomous slice. | `cd backend && pytest tests/unit/test_auth_config.py tests/unit/test_auth_jwks.py tests/unit/test_authorization.py -q`; mocked JWKS; revert core files/tests. |
| #2 `feat/entra-id-https-auth-02-identity` → `feat/entra-id-https-auth-01-auth` | RED, GREEN, REFACTOR migration, sync, disable and audit projection. | `cd backend && pytest tests/integration/test_identity_sync.py -q`; SQLite; revert migration and sync only. |
| #3 `feat/entra-id-https-auth-03-api` → `feat/entra-id-https-auth-02-identity` | RED, GREEN, REFACTOR endpoint matrix, `/users/me`, readiness/events. | `cd backend && pytest tests/api/test_authorization_matrix.py -q`; TestClient no-operation checks; revert endpoint dependencies. |
| #4 `feat/entra-id-https-auth-04-web` → `feat/entra-id-https-auth-03-api` | RED, GREEN, REFACTOR MSAL session, token provider, `can()`, routes and role UI. | `cd frontend && npx vitest run src/hooks/useAuth.test.ts src/routes/index.test.tsx`; mocked MSAL/MSW; revert frontend auth/guards. |
| #5 `feat/entra-id-https-auth-05-tls` → `feat/entra-id-https-auth-04-web` | RED, GREEN, REFACTOR secret hygiene and certificate-issuance manifests; redirect remains off. | `cd backend && pytest tests/test_k8s_manifests.py -q`; `kubectl kustomize k8s/overlays/prod`; revert issuer/TLS manifests. |
| #6 `feat/entra-id-https-auth-06-rollout` → `feat/entra-id-https-auth-05-tls` | RED, GREEN, REFACTOR deferred redirect gate and pilot/rollback runbook. | rendered-manifest test plus staging HTTPS/sign-in/four-role pilot; revert redirect patch/runbook, preserve valid TLS. |

## Phase 0: External Gates and Deferrals

- [ ] 0.1 Entra owners approve registrations, API scope/audience, issuer, roles, assignments, lifetime, and redirect URI before deployment; fixtures may unblock PR1–4 tests.
- [ ] 0.2 SQL operator approves migration/backup/restore before PR2 deployment; legacy identities remain unlinked and unprivileged.
- [ ] 0.3 Platform owners provide cert-manager, DNS solver secret delivery, issuer, DNS, and ingress support before PR5 deployment; require `Certificate Ready=True` and HTTPS probe before PR6 redirect.
- [ ] 0.4 Defer E2E framework, BFF/auth proxy, group-model redesign, committed credentials/certificates, and production enablement until all gates and pilot evidence pass.

## Phase 1: Slice Tasks

- [ ] 1.1 PR1: write failing mode, token rejection, one-refresh/503, and policy-matrix tests; implement minimum `backend/app/core/{config,security,authorization}.py`; refactor without sensitive logs.
- [ ] 1.2 PR2: write failing sync/disable/revocation/race/forbidden-field tests; implement `backend/app/models/schemas.py`, `backend/migrations/*`, and sync service; refactor transaction boundaries.
- [ ] 1.3 PR3: write failing 401/403-no-op, stats, and sanitized-`Me` tests; wire `backend/app/api/endpoints/{users,invoices,suppliers}.py` and `/readyz`; refactor shared dependencies.
- [ ] 1.4 PR4: write failing silent/login/logout/401 and permission-route tests; update `frontend/src/{main.tsx,hooks/useAuth.ts,api/client.ts,routes/*,components/Navbar.tsx,pages/*}`; refactor cleared state and guards.
- [ ] 1.5 PR5: write failing rendered-manifest secret/issuer/TLS/deferred-redirect tests; update `k8s/base/{configmap,secret,ingress,kustomization}.yaml` and `k8s/overlays/prod/*`; refactor overlays.
- [ ] 1.6 PR6: write the failing redirect-gate assertion; enable redirect only after the certificate/probe gate, run the pilot, and record slice-specific rollback evidence without restoring production `DEV_USER`.
