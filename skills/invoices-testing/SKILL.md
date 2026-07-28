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

## Structural Context (CodeGraph)

> Derived from the CodeGraph index (653 nodes, 1,321 edges). Use for impact analysis before edits.

### Hub symbols in this area
| Symbol | Location | Callers | Tests | Note |
|--------|----------|---------|-------|------|
| `test-utils.tsx` render wrapper | frontend/src/ | all component tests | — | #1 test infrastructure hub |
| `ApprovalDashboard.test.tsx` | co-located | — | covers ApprovalDashboard ✅ | Sorting, empty state, approval, delete |
| `SupplierDashboard.test.tsx` | co-located | — | covers SupplierDashboard ✅ | KPIs, charts, error state |
| `useAuth.test.ts` | co-located | — | covers useAuth ✅ | Role checks, localStorage |
| `test_invoices.py` | backend/tests/api/ | — | covers invoices endpoints ✅ | Upload, delete, list, 409, 503 |

### Per-symbol test coverage (CodeGraph-derived — honest report)

✅ Covered:
| Source symbol | Test file | Behavior verified |
|---------------|-----------|-------------------|
| `extract_invoice_data` (ai_service.py:128) | test_ai_service.py | Extraction, dev mode fallback |
| `StorageUploadError` (storage_service.py:23) | test_invoices.py + test_storage_service.py | Upload failure → 503 |
| `get_current_user` (security.py:72) | test_supplier_stats.py + conftest.py | Auth resolution |
| `User` model (schemas.py:99) | conftest.py + test_migrate_to_azure_sql.py + test_seed_db.py | User fixtures, migration |
| `useAuth` (useAuth.ts:20) | useAuth.test.ts | Role checks, localStorage |
| `SupplierDashboard` (SupplierDashboard.tsx:112) | SupplierDashboard.test.tsx + routes/index.test.tsx | KPIs, charts, routing |
| `uploadInvoiceHandlers` (UploadInvoice.handlers.ts:19) | UploadInvoice.test.tsx | MSW upload mock |
| `ApprovalDashboard` | ApprovalDashboard.test.tsx | Sorting, empty, approve, delete |

⚠️ Gaps (flagged by CodeGraph — recommended next tests):
| Source symbol | File:line | Gap |
|---------------|-----------|-----|
| `RoleChecker` | security.py:87 | No direct test — only transitively exercised |
| `UploadInvoice` (component) | UploadInvoice.tsx:24 | No direct component test — only MSW handlers tested |
| `Suppliers` (component) | Suppliers.tsx:15 | No covering test found |
| `Navbar` (component) | Navbar.tsx:6 | No covering test found |
| `User` (frontend interface) | useAuth.ts:5 | No direct test (interface only) |
| `suppliers.py` non-stats endpoints | suppliers.py | CRUD + delete not directly tested |
| `users.py` `get_current_user_profile` | users.py:14 | No direct backend test |
| `AuditLog` model | schemas.py:106 | No direct test |

### Call paths verified by tests
```
[Upload flow — test_invoices.py]
test → client.post("/api/invoices/upload", files=...)
  → upload_invoice → extract_invoice_data (mocked or dev mode)
  → storage.upload_pdf (mock_storage fixture)
  → db.add(Invoice) + db.commit
  → assert 200 + extracted_data

[Delete flow — test_invoices.py]
test → client.delete(f"/api/invoices/{id}")
  → delete_invoice → db.commit → _cleanup_uploaded_blob
  → assert db_session.commit called before mock_storage.delete_blob

[Frontend upload — UploadInvoice.test.tsx]
test → render(<UploadInvoice/>) with MSW handler
  → simulate file select → click upload
  → MSW returns mockExtractedData → assert extracted data form
```

### Cross-layer dependencies
- **409 duplicate test path** mocks the HTTP response but does NOT exercise the DB constraint (`uq_supplier_invoice`) that produces it in production. The backend `test_invoices.py` exercises the real constraint. Both layers are needed.
- **MSW handler path inconsistency:** global handlers use `/api/v1/users/me`, co-located handlers use `http://localhost:8000/api/invoices`. This is a drift risk — if the base URL changes, co-located handlers break silently.
- **testid contract:** the testid catalog in this skill MUST match components in `invoices-components`. Both skills list testids independently — drift here breaks tests silently.
- **Auth in tests:** `test-utils.tsx` injects a mock user via `useAuth` so `hasRole()` returns true. If a new page uses `hasRole('Clerk')` and the mock user doesn't have that role, the test will see the restricted message — update the mock user roles when adding Clerk-specific UI.

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
