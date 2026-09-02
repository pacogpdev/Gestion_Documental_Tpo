# Entra ID Authentication Specification

## Purpose

Define Entra identity, API-token validation, minimal local synchronization, and mode safety.

## Requirements

### Requirement: Separate SPA and API Token Contract

The system MUST use separate Entra SPA and API registrations. The SPA SHALL use MSAL authorization-code flow with PKCE and send an API access token; the API MUST accept only a signed access token for its configured tenant and audience, including effective app roles, and MUST reject an ID token, wrong audience, issuer, signature, or unknown signing key.

#### Scenario: API access token is accepted
- GIVEN an assigned user obtains an API access token through the SPA
- WHEN the token satisfies the API contract
- THEN the API authenticates the user and reads its effective roles

#### Scenario: Non-API token is rejected
- GIVEN a missing, invalid, or SPA ID token
- WHEN it reaches a protected API operation
- THEN the API returns 401 and performs no operation

### Requirement: Fail-Closed Production and Minimal Synchronization

Production MUST refuse startup or protected access when required identity configuration is absent or invalid and MUST NOT use `DEV_USER`. An explicit local-development mode MAY bypass Entra only outside production. Entra is the identity/grant source of truth; local records MUST contain only `oid`, tenant ID, display name/email, effective roles, sync time, audit linkage, and optional local disable status, and MUST NOT store tokens, groups, unused claims, or grant access independently. Local disable MUST deny immediately; Entra revocation MUST apply at token refresh/expiry and resynchronization.

#### Scenario: Production configuration is incomplete
- GIVEN production identity configuration is incomplete
- WHEN the service starts or receives protected traffic
- THEN it fails closed without a development identity

#### Scenario: Disabled or revoked user loses access
- GIVEN a synchronized user is locally disabled or Entra removes their grant
- WHEN the next access is evaluated under the applicable rule
- THEN access is denied and the local record cannot restore it

### Requirement: Strict TDD Evidence and Test Boundaries

Every acceptance test MUST be written red, made green with the minimum behavior, then refactored while green. Pytest unit tests SHALL cover token/config/sync rules; pytest integration tests SHALL cover HTTP authentication and the matrix; Vitest unit/component tests SHALL cover MSAL session and routes; rendered-manifest tests SHALL cover TLS, redirect, and secret hygiene. E2E is limited to a later pilot validating HTTPS, sign-in, and every role; the foundation MUST NOT introduce an E2E framework.

#### Scenario: Acceptance evidence is complete
- GIVEN a change slice is proposed for rollout
- WHEN its verification evidence is reviewed
- THEN each stated boundary shows red, minimal green, and refactor results

## Assumptions and External Prerequisites

Entra owners provide separate registrations, API scope/audience, app roles, assignments, and token lifetime. These are externally owned inputs, not implementation tasks.
