# Proposal: Frontend Critical Pages — Integration Tests

## Intent

Establish a comprehensive integration test suite for the three primary frontend pages (ApprovalDashboard, UploadInvoice, Suppliers) that validates every critical state (Loading, Empty, Error, Success) and key user interaction, using the MSW + test-utils infrastructure from the previous `frontend-testing-foundation` change.

---

## Scope

### In Scope

1. **Page test suites** (co-located `*.test.tsx` files):
   - `pages/ApprovalDashboard.test.tsx` — 7+ tests covering load, approve, reject, empty, error states
   - `pages/UploadInvoice.test.tsx` — 6+ tests covering upload flow, extracted data review, save, cancel, error states
   - `pages/Suppliers.test.tsx` — 6+ tests covering list load, create supplier, form toggle, empty, error states

2. **MSW page-level handlers** (`pages/*.handlers.ts`):
   - `ApprovalDashboard.handlers.ts` — invoice list + approve/reject endpoints
   - `UploadInvoice.handlers.ts` — upload + approve endpoints
   - `Suppliers.handlers.ts` — supplier CRUD endpoints

3. **Auth profiles in tests**: Each page tested with relevant `localStorage`-based auth state (Admin, Approver, Viewer) via `test-utils` `render()` `user` option.

4. **Cross-cutting scenario coverage**:
   - Loading states: Verify loading indicators appear/disappear
   - Empty states: Verify "no data" messages render
   - Error states: Verify API errors surface to user (alert or in-page)
   - Role-appropriate render: Verify correct content based on auth role

### Out of Scope

- **Route guard tests** — Routes have no `<ProtectedRoute>` wrapper; adding guards is a separate change
- **Navbar component tests** — Navigation behavior is separate from page content tests
- **E2E tests** — Playwright or Cypress journeys not included
- **Backend changes** — Pure frontend testing; no API modifications
- **Fixing uncovered bugs** — `Supplier Edit` dead button, `UploadInvoice` type bug, missing error states are logged as findings but NOT fixed here
- **`AppRoutes` integration tests** — Testing the full route tree with navigation flows is a future change
- **Accessibility tests** — `jest-axe` or similar not included

---

## Capabilities

### New Capabilities

- `frontend-page-approval-tests`: Integration test coverage for the ApprovalDashboard
- `frontend-page-upload-tests`: Integration test coverage for the UploadInvoice page
- `frontend-page-suppliers-tests`: Integration test coverage for the Suppliers page

### Modified Capabilities

- `frontend-msw-setup`: New page-specific handlers added to the handler organization pattern
- `frontend-testing-convention`: Page-level integration testing pattern documented

---

## Approach

### 1. Shared Page Handlers

Create `frontend/src/pages/ApprovalDashboard.handlers.ts`, `UploadInvoice.handlers.ts`, and `Suppliers.handlers.ts` exporting reusable MSW handlers for each page's API endpoints.

```ts
// ApprovalDashboard.handlers.ts
import { http, HttpResponse, delay } from 'msw';

export const approvalDashboardHandlers = [
  http.get('*/api/invoices', async () => {
    await delay(50);
    return HttpResponse.json([
      { id: '1', invoiceNumber: 'INV-001', supplierName: 'Acme Corp',
        date: '2026-06-01', totalAmount: 1500.00, currency: 'EUR', status: 'Pending' },
      // ...
    ]);
  }),
  http.patch('*/api/invoices/:id/approve', async () => {
    return HttpResponse.json({ success: true });
  }),
];
```

### 2. Test Structure

Each test file follows this pattern:

```tsx
import { render, screen, waitFor, fireEvent } from '../../test-utils';
import { server } from '../../mocks/server';
import { http, HttpResponse } from 'msw';
import ApprovalDashboard from './ApprovalDashboard';

const adminUser = { email: 'admin@test.com', fullName: 'Admin', roles: ['Admin'] };

describe('ApprovalDashboard', () => {
  afterEach(() => server.resetHandlers());

  it('shows loading then renders invoices', async () => {
    render(<ApprovalDashboard />, { user: adminUser, token: 'token' });
    
    // Loading state
    expect(screen.getByText('Loading invoices...')).toBeInTheDocument();
    
    // Success state
    await waitFor(() => {
      expect(screen.getByText('INV-001')).toBeInTheDocument();
    });
  });

  it('handles approve action', async () => {
    let patchedId = '';
    server.use(
      http.patch('*/api/invoices/:id/approve', async ({ params }) => {
        patchedId = params.id as string;
        return HttpResponse.json({ success: true });
      })
    );
    
    render(<ApprovalDashboard />, { user: adminUser, token: 'token' });
    
    await waitFor(() => {
      expect(screen.getByText('Approve')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Approve'));
    
    // Verify PATCH was called (via re-fetch or assertion)
    await waitFor(() => {
      expect(patchedId).toBeTruthy();
    });
  });

  it('shows empty state when no invoices', async () => {
    server.use(
      http.get('*/api/invoices', () => HttpResponse.json([]))
    );
    render(<ApprovalDashboard />, { user: adminUser, token: 'token' });
    
    await waitFor(() => {
      expect(screen.getByText('No invoices found.')).toBeInTheDocument();
    });
  });

  it('handles API error on load', async () => {
    server.use(
      http.get('*/api/invoices', () => HttpResponse.error())
    );
    render(<ApprovalDashboard />, { user: adminUser, token: 'token' });
    
    await waitFor(() => {
      // Currently only console.error — test documents gap
      expect(screen.queryByText('Loading invoices...')).not.toBeInTheDocument();
    });
  });
});
```

### 3. Auth Integration

Auth profiles are injected via `localStorage` through `test-utils` `render()` options:

```tsx
const adminUser   = { email: 'a@t.com', fullName: 'Admin', roles: ['Admin'] };
const approverUser = { email: 'ap@t.com', fullName: 'Approver', roles: ['Approver'] };
const viewerUser  = { email: 'v@t.com', fullName: 'Viewer', roles: ['Viewer'] };

render(<ApprovalDashboard />, { user: adminUser,  token: 'adm-token' });
render(<UploadInvoice />,      { user: approverUser, token: 'apr-token' });
render(<Suppliers />,          { user: viewerUser,  token: 'vw-token' });
```

The Navbar reads `useAuth()` from localStorage, so role-conditional links will render correctly when localStorage is populated.

---

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/pages/ApprovalDashboard.test.tsx` | **New** | 7+ integration tests |
| `frontend/src/pages/UploadInvoice.test.tsx` | **New** | 6+ integration tests |
| `frontend/src/pages/Suppliers.test.tsx` | **New** | 6+ integration tests |
| `frontend/src/pages/ApprovalDashboard.handlers.ts` | **New** | Shared MSW handlers for dashboard API |
| `frontend/src/pages/UploadInvoice.handlers.ts` | **New** | Shared MSW handlers for upload API |
| `frontend/src/pages/Suppliers.handlers.ts` | **New** | Shared MSW handlers for supplier API |
| `frontend/TESTING.md` | **Modified** | Document page-level integration test pattern |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MSW path matching with axios baseURL | Low | Tests silently use real network | Verify MSW intercepts in setup; use `*/api/` wildcard prefix |
| `jsdom` doesn't support File/FormData for upload tests | Medium | UploadInvoice tests cannot test file selection | Use `File` constructor (jsdom supports it); mock `createObjectURL` if needed; test upload button click separately |
| `alert()` calls in error paths block test runner | Low | `window.alert` not mocked | Stub `window.alert = vi.fn()` in test setup or per-suite `beforeEach` |
| Page tests exceed 400-line PR budget | Medium | Review load too high | Split into 2 PRs: (1) ApprovalDashboard + suppliers, (2) UploadInvoice (more complex form interactions) |
| `InvoiceData.id` type bug surfaces in tests | Low | Test fails due to TypeScript error | Cast or work around in test; document as known issue |

---

## Rollback Plan

Revert by deleting the 6 new files (3 test files + 3 handler files) and reverting `TESTING.md`. No other files are modified. Git revert on the commit range.

---

## Dependencies

- **`frontend-testing-foundation`** (MUST be complete and merged): MSW installed, `test-utils.tsx` with `render()` available, `setup.ts` with MSW lifecycle, Vitest configured
- No external dependencies beyond what's already in `package.json`

---

## Success Criteria

- [ ] `cd frontend && npm test` passes with all new tests green
- [ ] Each page has Happy Path tests: load, render data, primary interaction
- [ ] Each page has Edge Case tests: empty state, error state
- [ ] Loading indicators are verified for pages that have them (ApprovalDashboard, UploadInvoice)
- [ ] Auth profiles produce correct component rendering (Navbar links, content access)
- [ ] Tests are co-located per convention (`pages/Foo.test.tsx` + `pages/Foo.handlers.ts`)
- [ ] All tests import from `../../test-utils` (not directly from `@testing-library/react`)
- [ ] `window.alert` is stubbed in test setup to avoid blocking

---

## Discovery Findings (documented, not fixed)

During exploration, the following issues were identified in the pages under test:

| Issue | Location | Impact |
|-------|----------|--------|
| No visual error state | All 3 pages | Errors are `console.error` + `alert()` only — no in-page UI |
| No loading state | `Suppliers.tsx` | List renders empty or stale data during fetch |
| Dead Edit button | `Suppliers.tsx:121` | `<button>Edit</button>` has no `onClick` handler |
| Missing `id` in `InvoiceData` interface | `UploadInvoice.tsx:11-18` | `handleSave` references `extractedData.id` but `InvoiceData` has no `id` field |
| No route guards | `routes/index.tsx` | Navbar hides links by role, but direct URL access bypasses all guards |

These are logged here as findings for future changes but are NOT blockers for the test suite.
