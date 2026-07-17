# Supplier Stats API Specification

## Purpose

Define the supplier-level statistics contract used by the supplier dashboard. Annual metrics and monthly amounts MUST use the same trailing 12-month reporting window.

## Requirements

### Requirement: Supplier Stats Endpoint — returns all metrics

`GET /api/suppliers/{id}/stats` MUST return HTTP 200 for an existing supplier and MUST include the supplier name and tax ID, invoice count, annual accumulated amount, twelve ordered monthly amounts, annual percentage, grand total across suppliers, up to ten aggregated line items, Approved/Rejected/Pending counts, average invoice amount, and the highest-value invoice.

#### Scenario: Successful stats retrieval

- GIVEN an eligible user requests stats for an existing supplier with invoice data
- WHEN the request is processed
- THEN the response is 200 and contains every required metric for the 12-month reporting window

#### Scenario: Supplier not found

- GIVEN an eligible user requests stats for an unknown supplier ID
- WHEN the request is processed
- THEN the response is 404 and identifies that the supplier was not found

#### Scenario: Existing supplier with no invoices

- GIVEN an eligible user requests stats for a supplier with no invoices
- WHEN the request is processed
- THEN the response is 200 with zero totals/counts, twelve zero monthly amounts, no top invoice, and no top line items

### Requirement: Annual Percentage Calculation — percentage versus all suppliers

The endpoint MUST calculate the supplier’s annual percentage as its annual amount divided by the grand total of all suppliers’ annual amounts, multiplied by 100. If the grand total is zero, the percentage MUST be 0 and MUST NOT be undefined or an error.

#### Scenario: Percentage calculation

- GIVEN the supplier total is 1,200 and the grand total is 3,000
- WHEN supplier stats are requested
- THEN the response reports 40% and a grand total of 3,000

### Requirement: Top Line Items Aggregation — top ten by total amount

The endpoint MUST combine line items with the same description, report each description’s summed amount and invoice count, sort by descending summed amount, and return no more than ten entries.

#### Scenario: Top items ordering and aggregation

- GIVEN eleven or more line-item descriptions exist across the reporting window
- WHEN supplier stats are requested
- THEN the response contains the ten highest totals in descending order with correct per-description sums and invoice counts

### Requirement: Access Control — Admin and Approver only

The endpoint MUST allow users with the Admin or Approver role and MUST reject users with Clerk or Viewer roles with HTTP 403.

#### Scenario: Authorized roles retrieve stats

- GIVEN an authenticated Admin or Approver requests an existing supplier’s stats
- WHEN the request is processed
- THEN the response is successful and contains the requested metrics

#### Scenario: Unauthorized roles are denied

- GIVEN an authenticated Clerk or Viewer requests supplier stats
- WHEN the request is processed
- THEN the response is 403 and no statistics are returned
