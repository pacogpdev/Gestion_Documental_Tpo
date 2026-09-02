# Delta for Supplier Stats API

## MODIFIED Requirements

### Requirement: Access Control — Admin and Approver only

The endpoint MUST allow Admin, Approver, and Viewer roles and MUST reject Clerk with HTTP 403; its existing metrics contract remains unchanged.
(Previously: Allowed Admin and Approver only; rejected Clerk and Viewer.)

#### Scenario: Authorized roles retrieve stats
- GIVEN an authenticated Admin, Approver, or Viewer requests existing supplier statistics
- WHEN the request is processed
- THEN it returns 200 with the existing metrics contract

#### Scenario: Unauthorized roles are denied
- GIVEN an authenticated Clerk requests supplier statistics
- WHEN the request is processed
- THEN it returns 403 and no statistics
