# ApprovalDashboard Specification

## Purpose

Integration tests for the ApprovalDashboard page (`/dashboard`). Validates invoice listing, loading/empty states, and approve/reject status change actions via MSW + test-utils.

## Requirements

### Requirement: Data Loading — invoice list renders on mount

The test MUST verify that the page fetches and displays pending invoices on mount, showing a loading indicator while the request is in flight.

#### Scenario: Loading state then invoice rows

- GIVEN the API returns a list of invoices with mixed statuses
- WHEN the page mounts
- THEN "Loading invoices..." is shown in the table body during the request
- AND invoice rows render with invoice number, supplier, date, amount, and status badge
- AND the summary cards display correct Pending/Approved/Rejected counts

### Requirement: Empty State — no invoices message

The test MUST display a zero-state message when the API returns an empty list.

#### Scenario: Empty list shows "No invoices found."

- GIVEN the API returns an empty array `[]`
- WHEN the page mounts
- THEN "No invoices found." is displayed in the table body
- AND all summary cards show zero

### Requirement: Approval Action — approve a pending invoice

The test MUST call `PATCH /api/invoices/{id}/approve` with `status: "Approved"` when Approve is clicked, then refresh the invoice list.

#### Scenario: Approve button triggers API and refreshes

- GIVEN a pending invoice row is visible in the table
- WHEN the user clicks the "Approve" button
- THEN `PATCH /api/invoices/{id}/approve` is called with `{ status: "Approved" }`
- AND the invoice list is re-fetched after the API call succeeds

### Requirement: Rejection Action — reject a pending invoice

The test MUST call `PATCH /api/invoices/{id}/approve` with `status: "Rejected"` when Reject is clicked, then refresh the invoice list.

#### Scenario: Reject button triggers API and refreshes

- GIVEN a pending invoice row is visible in the table
- WHEN the user clicks the "Reject" button
- THEN `PATCH /api/invoices/{id}/approve` is called with `{ status: "Rejected" }`
- AND the invoice list is re-fetched after the API call succeeds
