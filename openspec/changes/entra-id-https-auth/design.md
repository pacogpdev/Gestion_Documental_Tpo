# Design: Entra ID HTTPS Authentication and Authorization

## Technical Approach

Replace implicit JWKS-driven development mode with explicit modes. A React MSAL PKCE SPA requests an API access token; FastAPI validates it, synchronizes a minimal identity, and is the authorization boundary. `/api/users/me` returns effective permissions so the UI does not recreate RBAC. TLS is introduced in two gated ingress stages.

## Architecture Decisions

| Decision | Choice and rationale |
|---|---|
| OAuth contract | Separate SPA/API registrations; MSAL PKCE requests `ENTRA_ID_API_SCOPE`. Validate RS256, `tid`, v2 issuer, exact API audience, expiry/not-before, and delegated scope. Refresh JWKS once on `kid` miss with bounded timeout/TTL; this rejects ID tokens. |
| Modes | `APP_ENV=local` plus `AUTH_MODE=local-dev` is the only bypass; it returns a clearly marked `DEV_USER`. `staging`/`production` require `AUTH_MODE=entra` and complete Entra settings at startup; unknown combinations fail startup/readiness. Kubernetes overlays never enable local-dev. |
| RBAC | `AuthorizationPolicy` is canonical in the API. It maps operations to roles and backs every dependency. `/users/me` returns its derived `permissions`; React uses `can(permission)`, never a duplicate role matrix. Backend matrix tests and frontend permission-contract tests detect drift. |
| Identity authority | Entra token identity and app roles are authoritative; local state is an audit/cache projection only. A local disable is the sole local override and always denies. No token, refresh token, group, or unneeded claim is persisted or logged. |
| TLS | DNS-01 `ClusterIssuer` and ingress-shim create `facturas-tls`. Apply TLS with redirect disabled; enable NGINX redirect only after `Certificate Ready=True` and HTTPS probe pass. |

## Data Flow

```text
React MsalProvider -> acquireTokenSilent(API scope) -> Axios token provider
  -> API validate/JWKS -> sync(tid, oid) -> AuthorizationPolicy -> endpoint
  <- /users/me {profile, roles, permissions} <- UI RequirePermission/can()
```

Silent failure clears the in-memory profile and shows redirect sign-in; logout invokes MSAL logout. A 401 requires a new session; 403 is access denied. The API returns 401 for missing/invalid/expired/wrong-audience tokens, 403 for disabled/no-permission users, and 503 for unavailable issuer/JWKS; none performs a business operation.

## Interfaces / Contracts

```ts
type Permission = 'read'|'statistics'|'upload'|'approve'|'delete'|'supplier_admin';
type Me = { email: string | null; fullName: string | null;
  roles: ('Admin'|'Approver'|'Clerk'|'Viewer')[]; permissions: Permission[] };
```

`/api/users/me` synchronizes then returns `Me`; it never exposes `oid`, token claims, or local IDs. Endpoint policy is: read all; statistics Admin/Approver/Viewer; upload Admin/Approver/Clerk; approve Admin/Approver; delete and supplier create/update/delete Admin only. Existing statistics payload remains unchanged.

## Data Model and Configuration

Extend `users` with nullable `tenant_id`, `entra_oid`, `is_disabled=false`, and `last_synced_at`; make `(tenant_id, entra_oid)` unique, permit nullable email, and retain names, roles, and `AuditLog.user_id`. A versioned idempotent migration adds `Clerk`, leaves legacy users unlinked, and grants none. Sync upserts by tenant/OID, atomically replaces recognized roles, preserves disable, audits, and retries a uniqueness race. Entra removal applies on next valid-token sync; local disable is immediate.

Non-secret config: `APP_ENV`, `AUTH_MODE`, `ENTRA_ID_TENANT_ID`, `ENTRA_ID_API_AUDIENCE`, `ENTRA_ID_ISSUER`, `ENTRA_ID_JWKS_URL`, `ENTRA_ID_API_SCOPE`, `VITE_ENTRA_{CLIENT_ID,TENANT_ID,API_SCOPE,REDIRECT_URI}`. Vite values are public. External secrets hold database, storage/AI, and DNS-solver credentials; remove committed secret values and DB credentials from ConfigMaps.

Structured events use outcome/reason/correlation and local audit ID only—never tokens, claims, email, or secrets. `/readyz` reports configuration readiness; certificate readiness is read from Kubernetes conditions.

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/app/core/{config,security,authorization}.py` | Modify/Create | validated modes, JWKS verifier, canonical policy |
| `backend/app/api/endpoints/{users,invoices,suppliers}.py` | Modify | profile contract, sync, complete policy dependencies |
| `backend/app/models/schemas.py`, `backend/migrations/*` | Modify/Create | identity fields and reversible migration |
| `frontend/src/{main.tsx,hooks/useAuth.ts,api/client.ts,routes/*}` | Modify/Create | MSAL provider, in-memory token provider, protected routes |
| `k8s/{base,overlays/prod}/**` | Modify/Create | external secrets, issuer, staged TLS patches |
| backend/frontend manifest tests | Modify/Create | isolated RED/GREEN coverage |

## Testing Strategy

Write RED first: pytest mode/JWKS/sync/disable units and HTTP role/no-operation tables; Vitest MSAL silent/login/logout/401 and route-permission mocks; rendered Kustomize secret/issuer/TLS/deferred-redirect tests. Isolate with per-test SQLite, overrides, fresh MSAL/QueryClient, cleared storage, and mocked network—never Entra, DNS, or certificates. No E2E framework; a later pilot covers HTTPS, sign-in, and four roles.

## Migration / Rollout

Deliver <=400-line slices: (1) config/JWT/policy; (2) migration/sync/audit; (3) endpoint matrix and `Me`; (4) MSAL/route/client; (5) secret hygiene/TLS issuance; (6) redirect/pilot runbook. Roll back only the current slice/migration with backup, preserve valid TLS, and never restore production `DEV_USER`.

## Threat Matrix

| Boundary | Applicability | Response / RED tests |
|---|---|---|
| Documentation-like paths | N/A | No executable classification. |
| Git repository selection | N/A | No VCS invocation. |
| Commit state | N/A | No commit automation. |
| Push state | N/A | No push automation. |
| PR commands | N/A | No PR or process integration. |

## Open Questions

- [ ] Gate: Entra owners supply registrations, scope/audience, role assignments, lifetime, and redirect URI.
- [ ] Gate: platform owners confirm DNS solver/secret ownership, cert-manager/ingress, and secret delivery.
- [ ] Gate: approve existing Azure SQL migration operator/tooling.
