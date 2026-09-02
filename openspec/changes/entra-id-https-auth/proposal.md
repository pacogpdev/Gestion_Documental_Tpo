# Proposal: Entra ID HTTPS Authentication and Authorization

## Intent

Replace the production `DEV_USER` bypass with fail-closed Microsoft Entra ID authentication, consistent RBAC, and trusted HTTPS so invoice access is auditable and least-privilege.

## Scope

### In Scope
- Separate SPA and API Entra registrations; MSAL PKCE access tokens for the API.
- Backend claim validation, resilient JWKS refresh, explicit local-development mode, and production configuration validation.
- Enforce the approved operation matrix: Admin all; Approver read/upload/approve-reject/stats; Clerk read/upload only; Viewer read-only, including dashboards/statistics.
- Synchronize minimal Entra profiles and effective roles locally; add ingress TLS through cert-manager and Let's Encrypt.

### Out of Scope
- Backend-for-frontend sessions, an auth proxy, tenant/group-model redesign, or committed credentials/certificates.
- Rebuilding invoice/supplier workflows or introducing an E2E framework in the foundation slice.

## Capabilities

### New Capabilities
- `entra-id-authentication`: SPA/API login, token validation, profile synchronization, and fail-closed production policy.
- `invoice-authorization`: API-authoritative role policy and role-aware UI.
- `ingress-tls`: cert-manager-issued Let's Encrypt TLS and HTTPS enforcement.

### Modified Capabilities
- `frontend-useauth-completion`: replace development-token hydration with Entra session lifecycle.
- `supplier-stats-api`: allow Viewer and deny Clerk access.
- `supplier-stats-dashboard`: expose statistics to Viewer and hide them from Clerk.

## Approach

Use Entra app roles in API access tokens; FastAPI remains the authorization boundary and UI guards are usability only. Entra is the source of truth for identity and grants; local records contain only `oid`, tenant ID, display name/email, effective roles, sync time, audit linkage, and an optional local disable flag. They never grant access, store tokens, or retain groups/unused claims. Local disable denies immediately; Entra revocation takes effect on refreshed/expired tokens and resynchronization.

Strict TDD: write backend JWT/config/RBAC tests, frontend MSAL/route tests, then rendered-manifest TLS/secret-hygiene tests before implementation. A later pilot validates HTTPS, sign-in, and each role.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `backend/app/core/{security,config}.py` | Modified | Entra validation and fail-closed modes |
| `backend/app/api/endpoints/` | Modified | Matrix enforcement and profile sync |
| `frontend/src/{hooks,api,components,routes}/` | Modified | MSAL login, token use, route UX |
| `k8s/{base,overlays/prod}/` | Modified | TLS, redirect, externalized secrets |
| `backend/tests/`, `frontend/src/**/*.test.*` | New/Modified | RED-GREEN-REFACTOR acceptance |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Incorrect Entra configuration locks out users | Med | Preflight validation and staged pilot |
| Role/config drift grants access | Med | Table-driven API tests; backend enforcement |
| Invalid certificate causes outage | Med | Verify issuer/DNS/secret before redirect |

## Rollout Plan

Deliver reviewable chained slices: (1) under-400-line auth/RBAC/TLS-test foundation; (2) MSAL and backend enforcement; (3) cert-manager TLS plus pilot. Enable production only after all gates pass.

## Rollback Plan

Revert the release slice, restore the previous ingress only after maintaining a valid certificate path, and disable the Entra deployment configuration. Never re-enable production `DEV_USER`; use controlled maintenance access instead.

## Dependencies

- Entra tenant owner, SPA/API registrations, roles, scope/audience, assignments, and approved token lifetime.
- cert-manager, Let's Encrypt issuer, DNS, and ingress-controller support.

## Success Criteria

- [ ] Production rejects missing/invalid identity configuration and unauthorized requests.
- [ ] Each operation obeys the approved matrix in backend and UI tests.
- [ ] No tokens, private keys, or identity secrets are committed; minimal local synchronization obeys revocation rules.
- [ ] HTTPS redirects, certificate issuance, and strict-TDD suites pass before rollout.
