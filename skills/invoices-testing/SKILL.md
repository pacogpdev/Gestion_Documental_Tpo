---
name: invoices-testing
description: >
  Unit and integration testing patterns for invoices app. Vitest, MSW, React Testing Library, co-located tests, backend tests with pytest.
  Trigger: When writing unit/integration tests, editing **/*.test.tsx or backend/tests/, Vitest, MSW.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Writing or editing tests in `frontend/src/**/*.test.tsx`
- Writing backend tests in `backend/tests/`
- Adding MSW handlers for test data
- Configuring Vitest or pytest

## Critical Patterns

### Co-location rule

Test files sit NEXT to their source file, never in a separate `__tests__/` directory:

```
pages/ApprovalDashboard.tsx        # Source
pages/ApprovalDashboard.test.tsx   # Test (same directory)
pages/ApprovalDashboard.handlers.ts # MSW handlers (same directory)
```

### Frontend test conventions

Always import from `test-utils`, never directly from `@testing-library/react`:

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../test-utils';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';
```

### Custom render wrapper

The `test-utils` module wraps components with `MemoryRouter` and injects auth state:

```tsx
render(<ApprovalDashboard />, {
  user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
  token: 'fake-jwt-token',
  route: '/approvals',
});
```

Available test-utils exports: `render`, `renderHook`, `screen`, `fireEvent`, `waitFor`, `cleanup`, `act`, `within`.

### Auth state injection

```tsx
// Authenticated as Admin
render(<Component />, {
  user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
  token: 'fake-jwt-token',
});

// Unauthenticated (no user, no token)
render(<Component />);

// Viewer role (restricted)
render(<Component />, {
  user: { email: 'viewer@test.com', fullName: 'Viewer User', roles: ['Viewer'] },
  token: 'fake-jwt-token',
});
```

### MSW handler patterns

**Global handlers** (applied before all tests, in `src/mocks/handlers.ts`):

```ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/v1/users/me', () => {
    return HttpResponse.json({
      email: 'test@example.com',
      fullName: 'Test User',
      roles: ['Admin'],
    });
  }),
];
```

**Co-located handlers** (page-specific test data):

```ts
// ApprovalDashboard.handlers.ts
import { http, HttpResponse } from 'msw';

export const approvalDashboardHandlers = [
  http.get('http://localhost:8000/api/invoices', () => {
    return HttpResponse.json([
      { id: 'inv-001', invoiceNumber: 'INV-2024-001', supplierName: 'Acme Corp',
        date: '2024-01-15', totalAmount: 1250.0, currency: 'USD', status: 'Pending' },
    ]);
  }),
];
```

**Inline override** (for single-test variations):

```tsx
it('shows empty state', async () => {
  server.use(
    http.get('http://localhost:8000/api/invoices', () => HttpResponse.json([]))
  );
  render(<ApprovalDashboard />, { ... });
  await waitFor(() => expect(screen.getByTestId('empty-state')).toBeInTheDocument());
});
```

### testid convention

Every interactive or observable element MUST have a `data-testid`:

```tsx
<div data-testid="loading-indicator">Loading...</div>
<tr data-testid={`invoice-row-${inv.id}`}>
<button data-testid={`approve-btn-${inv.id}`}>
<button data-testid="delete-btn-inv-001">
<th data-testid="sort-date">
<th data-testid="sort-amount">
<input data-testid="search-input">
<div data-testid="empty-state">
<div data-testid="server-error">
```

### Test organization (describe blocks)

```tsx
describe('ApprovalDashboard', () => {
  beforeEach(() => { localStorage.clear(); });

  describe('2.2 — Data Loading', () => {
    it('shows loading indicator then renders invoice rows and summary cards', async () => { ... });
  });

  describe('2.3 — Empty State', () => {
    it('shows empty state message', async () => { ... });
  });

  describe('2.4 — Approval Action', () => {
    it('calls PATCH with Approved status', async () => { ... });
  });
});
```

### TDD workflow on this project

1. **RED** — Write failing test first
2. **GREEN** — Write minimum implementation to pass
3. **REFACTOR** — Clean up without changing behavior

### Backend test conventions

Tests use `backend/tests/` directory with pytest:

```python
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
```

### Sorting test pattern

```tsx
it('sorts ascending on first click (oldest first)', async () => {
  server.use(http.get('http://localhost:8000/api/invoices',
    () => HttpResponse.json(sortTestInvoices)));

  render(<ApprovalDashboard />, { ... });
  await waitFor(() => expect(screen.getByText('INV-003')).toBeInTheDocument());

  fireEvent.click(screen.getByTestId('sort-date'));

  const rows = screen.getAllByTestId(/^invoice-row-/);
  await waitFor(() => {
    expect(rows[0]).toHaveTextContent('INV-001');
    expect(rows[2]).toHaveTextContent('INV-003');
  });
});
```

### Duplicate error test pattern

```tsx
it('shows duplicate invoice error when server responds with 409', async () => {
  server.use(
    http.post('http://localhost:8000/api/invoices/upload', () =>
      HttpResponse.json(
        { detail: "Duplicate invoice: invoice number '...' already exists for supplier '...'." },
        { status: 409 }
      )
    )
  );
  // ...
  expect(screen.getByTestId('server-error')).toHaveTextContent('already exists');
});
```

### Vitest configuration

```ts
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
});
```

### Running tests

```bash
cd frontend
npx vitest run               # Run all once
npx vitest                    # Watch mode
npx vitest run --reporter=verbose  # Verbose output

cd backend
pytest -v                     # Run backend tests
pytest tests/ -v              # Run specific test file
```

## File Structure

```
frontend/src/
├── test-utils.tsx          # Custom render with MemoryRouter + auth injection
├── test/
│   └── setup.ts            # Vitest setup (MSW server lifecycle)
├── mocks/
│   ├── handlers.ts         # Global MSW handlers
│   └── server.ts           # MSW server (setupServer)
├── pages/
│   ├── ApprovalDashboard.test.tsx    # Co-located tests
│   ├── ApprovalDashboard.handlers.ts # Co-located MSW data
│   ├── UploadInvoice.test.tsx
│   ├── UploadInvoice.handlers.ts
│   ├── Suppliers.test.tsx
│   └── Suppliers.handlers.ts

backend/
└── tests/
    └── api/
        └── test_invoices.py  # Pytest backend tests
```
