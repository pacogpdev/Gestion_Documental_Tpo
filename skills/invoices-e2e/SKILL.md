---
name: invoices-e2e
description: >
  E2E testing patterns with Playwright for invoices app. Smoke tests, critical path coverage, test isolation.
  Trigger: When writing E2E tests, editing files in e2e/, or configuring Playwright for smoke/integration tests.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Writing or editing E2E tests in `e2e/`
- Adding smoke tests for critical user flows
- Configuring Playwright

## Getting Started

This project does not yet have E2E tests configured. When adding them, follow these conventions.

### Setup

```bash
# Install Playwright (when ready)
npm init playwright@latest -- --ct
# or: npx playwright install
```

### File structure (when created)

```
e2e/
├── base-page.ts                    # Parent class for all Page Objects
├── helpers.ts                      # resetDatabase(), shared utilities
├── invoices/
│   ├── invoices-page.ts           # Page Object for invoice dashboard
│   ├── invoices.spec.ts           # ALL invoice tests (one file)
│   └── invoices.md                # Test documentation
├── playwright.config.ts
```

### Critical paths to cover (future)

| Flow | Scenario |
|------|----------|
| Upload | Upload a valid PDF, verify extraction review form |
| Approval | Approve a pending invoice, verify status changes |
| Rejection | Reject a pending invoice |
| Delete | Delete an invoice, verify it disappears |
| Duplicate | Upload same invoice twice, see 409 error |
| Pagination | Navigate pages when 15+ invoices exist |
| Sorting | Sort by date and amount, verify order |
| Search | Filter by invoice number or supplier name |

## File Structure (planned)

```
e2e/
├── playwright.config.ts        # Playwright configuration
├── base-page.ts                # Base Page Object class
├── helpers.ts                  # Test utilities
└── invoices/
    ├── invoices-page.ts        # Invoice Page Object
    ├── invoices.spec.ts        # E2E tests
    └── invoices.md             # Test documentation
```
