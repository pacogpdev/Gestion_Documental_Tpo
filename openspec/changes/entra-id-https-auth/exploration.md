## Exploration: Microsoft Entra ID authentication, RBAC, and Kubernetes HTTPS

### Confirmed Facts
- The backend enters a fail-open development path whenever `ENTRA_ID_JWKS_URL` is empty: `OptionalHTTPBearer` accepts no credential, `get_current_user` returns `DEV_USER` as `Admin`, and `RoleChecker` skips authorization.
- When configured, the backend validates an RS256 bearer JWT against a cached JWKS and checks `audience=ENTRA_ID_CLIENT_ID` and the tenant v1 issuer. The cache has no refresh-on-unknown-key or expiry policy.
- The React client has no Entra/MSAL dependency or login flow. `Navbar` calls `/users/me` and saves a literal `dev-token`; `useAuth` and the Axios interceptor persist profile and token in `localStorage`.
- Backend RBAC and frontend rendering differ: the backend permits `Clerk` to upload/delete invoices, while the frontend role type omits `Clerk` and its Upload UI permits `Approver`/`Admin`. Supplier create/update are authenticated but have no `RoleChecker`.
- React routes are not protected; UI hiding is not an authorization boundary. The backend is the effective enforcement point for routes that declare `RoleChecker`.
- The Kubernetes `Ingress` uses `ingressClassName: nginx` and routes the public hostname, but contains no `spec.tls` block or HTTPS redirect annotation. TLS would terminate at the ingress; the frontend nginx and backend currently communicate by HTTP inside the cluster.
- Backend Pods load environment from `backend-config` and `backend-secrets`. The production overlay currently contains database connection credentials in a ConfigMap patch; do not reproduce or extend that pattern for identity material.
- Strict TDD is enabled. Pytest and Vitest are available; no Playwright/E2E setup exists.

### Assumptions and Unanswered Product/Security Decisions
- Assumption: the production domain and nginx ingress controller remain the intended public edge. DNS ownership, controller TLS support, and certificate automation are unverified.
- Decide the Entra tenant model, the owning team, and whether access is assigned directly, through groups, or both.
- Decide whether to use separate SPA and API app registrations (recommended) or one registration; define the API Application ID URI, delegated scope, accepted token version, and exact audience.
- Approve the role matrix for every API operation, especially Clerk upload/delete, Approver supplier access, and Supplier create/update. Decide whether `Viewer` may access dashboard, invoices, suppliers, and supplier statistics.
- Decide production authentication policy: local development may retain an explicitly selected development mode, but production must fail closed when Entra configuration is absent or invalid.
- Decide the certificate issuer/provisioning path, renewal ownership, and the secret name. A TLS secret needs `tls.crt` and `tls.key`; no certificate manager is confirmed in this cluster.
- Decide whether Entra object ID (`oid`) must be persisted for auditing/provisioning. Existing database User/Role tables are not the active authorization source.

### Current State
The intended production path is bearer JWT validation in FastAPI, but production can still silently become the all-Admin development path if JWKS configuration is omitted. The frontend cannot obtain a real access token, so it can only bootstrap the development user. The ingress exposes HTTP only. The stack is otherwise compatible with a browser SPA acquiring an Entra access token and calling the existing same-origin `/api` route.

### Affected Areas
- `backend/app/core/security.py` — replace configuration-as-mode detection with explicit fail-closed policy; validate Entra access-token claims and make JWKS rotation resilient.
- `backend/app/core/config.py` — model identity authority, API audience/scope, allowed issuers, and explicit local-development policy.
- `backend/app/api/endpoints/{users,invoices,suppliers}.py` — normalize Entra claims for `/users/me` and apply the approved role policy consistently.
- `frontend/src/hooks/useAuth.ts`, `frontend/src/api/client.ts`, `frontend/src/components/Navbar.tsx`, `frontend/src/routes/index.tsx` — acquire/renew real API tokens, replace dev bootstrap, support all approved roles, and guard routes for UX.
- `frontend/package.json` — add an Entra-compatible SPA authentication library if the recommended approach is approved.
- `k8s/base/ingress.yaml`, `k8s/base/{configmap,secret}.yaml`, `k8s/overlays/prod/` — TLS termination, HTTPS redirect, non-secret identity configuration, and externalized secret delivery.
- `backend/tests/`, `frontend/src/**/*.test.*`, and future `e2e/` — enforce the authentication contract before implementation under strict TDD.

### Approaches
1. **SPA bearer tokens with Entra MSAL and a protected API** — Register a public SPA and a resource API, use authorization code flow with PKCE, acquire the API access token silently when possible, and validate that access token in FastAPI. Put Entra app roles in the API token and retain backend role checks as the authority.
   - Pros: Fits the existing React static deployment and Bearer-token API design; no backend session store; Microsoft recommends MSAL/PKCE for SPAs; smallest architectural shift.
   - Cons: Requires careful token-cache/XSS posture, two app registrations and consent/role assignment, plus a coordinated frontend/backend rollout.
   - Effort: High

2. **Backend-for-frontend session model** — Have FastAPI perform OIDC authorization-code handling and issue secure same-site session cookies; the browser never handles an access token directly.
   - Pros: Stronger browser token isolation and centralized session/logout policy.
   - Cons: Introduces server-side session/callback/CSRF design and changes the static SPA/API boundary substantially.
   - Effort: High

3. **Ingress-only authentication proxy** — Delegate authentication to an ingress/OAuth proxy and forward identity headers to FastAPI.
   - Pros: Centralized edge sign-in and can protect multiple applications.
   - Cons: Not supported by the current manifests, needs trusted-header hardening and proxy operations, and still requires backend authorization design.
   - Effort: High

### Recommendation
Adopt **Approach 1** with separate SPA and API registrations, Entra API access tokens, and backend-enforced app roles. It preserves the current browser-to-FastAPI Bearer contract while removing the production bypass. Keep a deliberately named local-development mode only; deployment validation must reject production if it selects that mode or lacks complete identity configuration.

TLS should terminate at the nginx ingress using a `kubernetes.io/tls` Secret and controller-supported HTTPS redirect. Prefer externally provisioned/renewed certificates if the cluster already has an approved certificate controller; otherwise make manual secret rotation an explicit operational runbook, not a committed secret.

### Test Strategy (Strict TDD)
- **Backend RED tests first:** explicit production configuration rejection; no-token `401`; valid mocked JWKS token; expired, wrong-audience, wrong-issuer, malformed, and unknown-`kid` token rejection; JWKS refresh behavior; `/users/me` claim mapping; and a table-driven operation-by-role matrix.
- **Frontend RED tests first:** sign-in bootstrap, silent access-token acquisition, interaction-required/expired-token handling, logout, interceptor token attachment, protected-route UX, and Admin/Approver/Clerk/Viewer rendering. Tests must mock MSAL and must not contain real tokens.
- **Deployment tests before manifest changes:** render the production Kustomize overlay and assert the hostname, `spec.tls` secret reference, HTTPS redirect annotation, and absence of committed certificate/private-key or identity-secret values.
- **Release verification:** add a later Playwright/pilot slice for HTTPS redirect, unauthenticated redirect, each assigned role's allowed/forbidden API call, and certificate validity. No E2E framework exists today.

### First Slice Scope
Create a reviewable foundation slice (target under the 400-line budget) that adds the explicit auth-mode/configuration contract, backend JWT/role-policy tests, role-matrix normalization, and TLS manifest tests. Do not activate Entra or remove the current local path in production until the subsequent MSAL login slice and the deployment/certificate slice are verified together. Forecast: chained slices are likely required; approval is needed before task planning because delivery strategy is ask-always.

### Risks
- A configuration-only switch can leave all production traffic as `DEV_USER` Admin; production must fail closed and rollout must be gated.
- Audience, issuer, scopes, app-role claim emission, and group/role assignment are Entra tenant decisions that cannot be inferred from source.
- Current UI and API role rules drift; changing only UI is insecure and changing only API produces broken user workflows.
- The current infinite JWKS cache can reject rotated signing keys; availability and key-rotation behavior need explicit tests.
- TLS configuration is controller and certificate-issuer dependent; enabling a TLS block without a valid secret/certificate can cause an outage.
- A production database credential is present in a ConfigMap patch. Treat it as exposed and rotate/migrate it outside this feature's code path.

### Ready for Proposal
No — first obtain decisions for Entra app-registration ownership/model, approved per-operation role matrix, production fail-closed policy, and certificate provisioning/renewal. Once confirmed, proceed to `sdd-propose` and plan chained delivery slices within the 400-line review budget.
