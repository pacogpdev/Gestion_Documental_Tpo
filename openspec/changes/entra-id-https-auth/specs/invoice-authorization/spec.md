# Invoice Authorization Specification

## Purpose

Define the API-authoritative Entra-role operation policy and role-aware UI.

## Requirements

### Requirement: Approved Operation Matrix

The API MUST enforce this matrix; UI guards MUST mirror it for usability and MUST NOT be relied on for authorization.

| Operation | Admin | Approver | Clerk | Viewer |
|---|---|---|---|---|
| Read invoices/suppliers | Allow | Allow | Allow | Allow |
| Statistics/dashboard | Allow | Allow | Deny | Allow |
| Upload | Allow | Allow | Allow | Deny |
| Approve/reject | Allow | Allow | Deny | Deny |
| Delete or supplier administration | Allow | Deny | Deny | Deny |

#### Scenario: Allowed operations succeed
- GIVEN an authenticated role and an operation marked Allow
- WHEN the role invokes the API
- THEN the API authorizes it and the UI exposes its action

#### Scenario: Denied operations cannot be bypassed
- GIVEN an authenticated role and an operation marked Deny
- WHEN the role calls the API directly or opens its route
- THEN the API returns 403 and the UI hides or blocks the action

### Requirement: Authorization Is Observable

The system MUST retain audit linkage for synchronized identities and MUST make authentication, authorization, synchronization, and configuration/certificate readiness outcomes available for rollout review without exposing tokens or secrets.

#### Scenario: Rollout review
- GIVEN a pilot access attempt or synchronization result
- WHEN an operator reviews its outcome
- THEN identity and authorization status are traceable through audit linkage
