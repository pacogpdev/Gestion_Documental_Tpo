# Exploration: Frontend Critical Pages — Integration Testing

## Page Mapping

### 1. ApprovalDashboard (`/dashboard`)

| Aspect | Details |
|--------|---------|
| **API calls** | `GET /api/invoices` (list all), `PATCH /api/invoices/{id}/approve` (change status) |
| **Key interactions** | Page load triggers fetch; clicking "Approve" or "Reject" sends PATCH, then re-fetches |
| **Loading state** | `"Loading invoices..."` — rendered in `<td>` with `colSpan=6` |
| **Empty state** | `"No invoices found."` — shown when `invoices.length === 0` AND `loading === false` |
| **Error state** | **MISSING** — only `console.error()`; no visual feedback to the user |
| **Success state** | Invoice table with status badges (Pending/Approved/Rejected) and action buttons for Pending items |
| **Role access** | Route/component has NO guard. Navbar shows Dashboard link to all roles. No restriction. |
| **Edge cases** | API 500 on initial fetch; API 500 on approve/reject PATCH; empty invoices array; mixed statuses |

### 2. UploadInvoice (`/upload`)

| Aspect | Details |
|--------|---------|
| **API calls** | `POST /api/invoices/upload` (multipart/form-data), `PATCH /api/invoices/{id}/approve` (save extracted data) |
| **Key interactions** | File selection → "Upload & Analyze" button → fill/edit extracted data form → "Approve & Save" or "Cancel" |
| **Loading state** | Button shows `"Processing AI Extraction..."` and is `disabled` while `uploading === true` |
| **Empty state** | N/A — initial state is the upload drop zone |
| **Error state** | `alert()` calls only — no in-page error rendering |
| **Success state** | After upload: extracted data form with editable fields and line items table. After save: `alert('Invoice approved and saved!')` |
| **Role access** | Route has NO guard. Navbar shows link only for `Approver` or `Admin`. Viewer can navigate directly via URL. |
| **Edge cases** | No file selected + click upload; API 500 on upload; API 500 on save; `InvoiceData` lacks `id` field but `handleSave` references `extractedData.id` (type bug); line item editing with overlapping state mutations |

### 3. Suppliers (`/suppliers`)

| Aspect | Details |
|--------|---------|
| **API calls** | `GET /api/suppliers` (list), `POST /api/suppliers` (create) |
| **Key interactions** | Page load → fetch list; click "+ Add Supplier" → toggle form; fill form → submit → create + re-fetch |
| **Loading state** | **MISSING** — no `loading` state variable, no loading indicator at all |
| **Empty state** | `"No suppliers found."` — shown when `suppliers.length === 0` (after fetch completes) |
| **Error state** | `console.error()` + `alert()` only — no in-page error |
| **Success state** | Supplier table + inline creation form |
| **Role access** | Route has NO guard. Navbar shows link only for `Admin`. Approver/Viewer can navigate directly via URL. |
| **Edge cases** | API 500 on fetch; API 500 on create; empty initial form submission validation (HTML `required` only); Edit button exists but has NO onClick handler (dead UI element) |

---

## Testing Strategy

### Using `test-utils.tsx`

The shared `render()` function already provides:
- `MemoryRouter` wrapping (with `route` param for initial URL)
- `localStorage` auth pre-population (`user` + `token` params)

**What we need beyond current `test-utils`**: The current `render` does NOT wrap with an `AuthContext` provider — `useAuth` reads directly from `localStorage`. This works for these pages since they only call `apiClient` (which reads `auth_token` from localStorage via interceptor), but the Navbar component embedded in the route tree also calls `useAuth`. Tests rendering full pages via `AppRoutes` or with `Navbar` will need `localStorage` populated for `useAuth` to return a user.

**Pattern for page tests**:
```tsx
import { render, screen, waitFor } from '../../test-utils';
import { server } from '../../mocks/server';
import { http, HttpResponse } from 'msw';

// Set auth state
const adminUser = { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] };

it('renders invoice list', async () => {
  server.use(
    http.get('*/api/invoices', () => HttpResponse.json([
      { id: '1', invoiceNumber: 'INV-001', supplierName: 'Acme', ... }
    ]))
  );
  render(<ApprovalDashboard />, { user: adminUser, token: 'fake-token' });
  
  await waitFor(() => {
    expect(screen.getByText('INV-001')).toBeInTheDocument();
  });
});
```

### MSW Handler Requirements

| Endpoint | Handler needed | Response shape |
|----------|---------------|----------------|
| `GET /api/invoices` | `http.get('*/api/invoices')` | `Invoice[]` |
| `PATCH /api/invoices/{id}/approve` | `http.patch('*/api/invoices/*/approve')` | `{ success: true }` |
| `POST /api/invoices/upload` | `http.post('*/api/invoices/upload')` | `InvoiceData` |
| `GET /api/suppliers` | `http.get('*/api/suppliers')` | `Supplier[]` |
| `POST /api/suppliers` | `http.post('*/api/suppliers')` | `Supplier` |

### Auth State Integration

Three distinct auth profiles for tests:

| Profile | `user.roles` | Can access Dashboard | Can access Upload | Can access Suppliers |
|---------|-------------|---------------------|-------------------|---------------------|
| **Admin** | `['Admin']` | Yes | Yes (link shown) | Yes (link shown) |
| **Approver** | `['Approver']` | Yes | Yes (link shown) | No link (but route accessible via URL) |
| **Viewer** | `['Viewer']` | Yes | No link (route accessible via URL) | No link (route accessible via URL) |

### Happy Path Tests

1. **ApprovalDashboard**: Loads and displays invoices; Approve button changes status; Reject button changes status; summary cards reflect counts correctly.
2. **UploadInvoice**: Upload flow → file selected → upload triggered → extracted data shown → edit fields → save.
3. **Suppliers**: Loads supplier list; Add Supplier form toggle; Create supplier → appears in list.

### Edge Case Tests

1. **ApprovalDashboard**: API 500 on load → should show error (currently missing — test will fail until fixed); API 500 on approve → should show error alert; Empty invoice list; Single row edge cases (approve last pending item).
2. **UploadInvoice**: No file + click upload; API 500 on upload; API 500 on save; Cancel after extraction resets to upload view.
3. **Suppliers**: API 500 on fetch; API 500 on create; form validation with empty required fields.

### Cross-cutting Issues to Document

1. **No error states**: All three pages lack visual error handling — only `console.error()` + `alert()`. Tests for error states will expose this gap.
2. **Route guards missing**: Navbar hides links by role, but routes have no `<ProtectedRoute>` wrapper. Direct URL access bypasses role checks.
3. **Suppliers Edit button is dead**: Has no `onClick` handler — non-functional UI element.
4. **UploadInvoice type bug**: `InvoiceData` interface lacks `id` but `handleSave` references `extractedData.id`.

---

## Effort Estimate

| Component | Test files | Happy Path | Edge Cases | Auth Variants | Estimated tests |
|-----------|-----------|------------|------------|---------------|-----------------|
| ApprovalDashboard | 1 | 3 | 4 | 1 (no role gate) | 7 |
| UploadInvoice | 1 | 2 | 4 | 1 (no role gate) | 6 |
| Suppliers | 1 | 3 | 3 | 1 (no role gate) | 6 |
| Shared MSW handlers | 1 | — | — | — | — |
| **Total** | **4 files** | **8** | **11** | **3** | **~19 tests** |

**Total estimated lines**: ~400 (handlers + tests)
