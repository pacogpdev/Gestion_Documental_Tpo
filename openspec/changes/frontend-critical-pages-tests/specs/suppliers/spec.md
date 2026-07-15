# Suppliers Specification

## Purpose

Integration tests for the Suppliers page (`/suppliers`). Validates supplier listing, role-based access controls, and dynamic search/filtering via MSW + test-utils.

## Requirements

### Requirement: Listing — supplier list renders on mount

The test MUST verify that the page fetches and displays all suppliers on mount.

#### Scenario: Supplier rows render from API response

- GIVEN the API returns a list of suppliers with name, tax ID, and email
- WHEN the page mounts
- THEN `GET /api/suppliers` is called
- AND supplier rows render in the table with name, tax ID, and email columns

### Requirement: Role Access — Admin-only Add Supplier button

The test MUST hide the "+ Add Supplier" button for non-Admin roles.

#### Scenario: Add Supplier hidden for non-Admin roles

- GIVEN the user has `['Viewer']` or `['Approver']` roles in localStorage
- WHEN the page renders
- THEN the "+ Add Supplier" button is not present in the DOM
- AND the supplier list table still renders normally

### Requirement: Search/Filter — dynamic filtering by search term

The test MUST filter the supplier list in real-time as the user types a search term.

#### Scenario: Search filters suppliers dynamically

- GIVEN suppliers are loaded and rendered in the table
- WHEN the user types a search term into the filter input
- THEN only suppliers whose name, tax ID, or email match the term remain visible
- AND non-matching supplier rows are removed from the DOM
