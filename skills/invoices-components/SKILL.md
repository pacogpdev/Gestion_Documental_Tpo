---
name: invoices-components
description: >
  React + TypeScript component patterns for invoices. Page components, API client, auth hooks, pagination, sorting.
  Trigger: When editing files in frontend/src/pages/ or frontend/src/components/, adding page/component logic.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Creating or editing page components in `frontend/src/pages/`
- Creating or editing shared components in `frontend/src/components/`
- Adding interactivity, API calls, sorting, filtering, or pagination

## Critical Patterns

### Page component structure

```tsx
import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';

interface Invoice {
  id: string;
  invoiceNumber: string;
  supplierName: string;
  date: string;
  totalAmount: number;
  currency: string;
  status: 'Pending' | 'Approved' | 'Rejected';
}

const MyPage: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/invoices');
      setInvoices(response.data);
    } catch (error) {
      console.error('Failed to fetch', error);
    } finally {
      setLoading(false);
    }
  };

  // ...render
};

export default MyPage;
```

### API client usage

The Axios client auto-injects JWT and base URL:

```tsx
import apiClient from '../api/client';

// GET
const { data } = await apiClient.get('/invoices');

// POST with file (FormData auto-detected)
const formData = new FormData();
formData.append('file', selectedFile);
const { data } = await apiClient.post('/invoices/upload', formData);

// PATCH
await apiClient.patch(`/invoices/${id}/approve`, { status: 'Approved' });

// DELETE
await apiClient.delete(`/invoices/${id}`);
```

### Auth patterns

```tsx
import { useAuth } from '../hooks/useAuth';

const { user, login, logout, hasRole } = useAuth();

if (hasRole('Admin')) { /* show admin controls */ }
```

### Sorting pattern

```tsx
type SortKey = 'date' | 'amount';
type SortDir = 'asc' | 'desc';

interface SortConfig {
  key: SortKey;
  direction: SortDir;
}

const [sortConfig, setSortConfig] = useState<SortConfig>({ key: 'date', direction: 'desc' });

const handleSort = (key: SortKey) => {
  setSortConfig(prev => {
    if (prev?.key === key) {
      return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' };
    }
    return { key, direction: 'asc' };
  });
};

// Apply sort before pagination
const sortedInvoices = [...filteredInvoices].sort((a, b) => {
  const dir = sortConfig.direction === 'asc' ? 1 : -1;
  if (sortConfig.key === 'date') {
    return (new Date(a.date).getTime() - new Date(b.date).getTime()) * dir;
  }
  return (a.totalAmount - b.totalAmount) * dir;
});
```

### Sortable column header with always-visible arrows

```tsx
<th
  data-testid="sort-date"
  onClick={() => handleSort('date')}
  className="p-4 font-semibold cursor-pointer hover:text-slate-900 select-none"
  aria-sort={sortConfig?.key === 'date'
    ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending')
    : undefined}
>
  Date <span className="text-xs ml-0.5">
    <span className={sortConfig?.key === 'date' && sortConfig.direction === 'asc'
      ? 'text-blue-600' : 'text-slate-300'}>▲</span>
    <span className={sortConfig?.key === 'date' && sortConfig.direction === 'desc'
      ? 'text-blue-600' : 'text-slate-300'}>▼</span>
  </span>
</th>
```

### Pagination pattern (15/page)

```tsx
const PAGE_SIZE = 15;
const [page, setPage] = useState(1);

// Reset page on filter/sort change
useEffect(() => { setPage(1); }, [statusFilter, searchQuery, sortConfig]);

const totalPages = Math.max(1, Math.ceil(sortedInvoices.length / PAGE_SIZE));
const safePage = Math.min(page, totalPages);
const pageStart = (safePage - 1) * PAGE_SIZE;
const pageEnd = Math.min(pageStart + PAGE_SIZE, sortedInvoices.length);
const pageInvoices = sortedInvoices.slice(pageStart, pageEnd);
```

### Search/filter pattern

```tsx
const [searchQuery, setSearchQuery] = useState('');

const query = searchQuery.toLowerCase().trim();
const filteredInvoices = query
  ? invoices.filter(inv =>
      inv.invoiceNumber.toLowerCase().includes(query) ||
      inv.supplierName.toLowerCase().includes(query))
  : invoices;
```

### Error handling for file upload (409 / 500)

```tsx
try {
  const response = await apiClient.post('/invoices/upload', formData);
  // success path
} catch (error: any) {
  if (error.response?.status === 409) {
    setError(error.response.data.detail); // "Duplicate invoice..."
  } else {
    setError('An unexpected error occurred while uploading the invoice.');
  }
}
```

### Status badge pattern

```tsx
<span className={`px-2 py-1 rounded-full text-xs font-bold ${
  inv.status === 'Approved' ? 'bg-green-100 text-green-700' :
  inv.status === 'Rejected' ? 'bg-red-100 text-red-700' :
  'bg-orange-100 text-orange-700'
}`}>
  {inv.status}
</span>
```

### Co-located MSW handlers

For page-specific test data, create co-located handler files:

```tsx
// ApprovalDashboard.handlers.ts
import { http, HttpResponse } from 'msw';

export const approvalDashboardHandlers = [
  http.get('http://localhost:8000/api/invoices', () => {
    return HttpResponse.json([/* test data */]);
  }),
];
```

Use inline `server.use()` for single-test overrides.

## Structural Context (CodeGraph)

> Derived from the CodeGraph index (653 nodes, 1,321 edges). Use for impact analysis before edits.

### Hub symbols in this area
| Symbol | Location | Callers | Tests | Note |
|--------|----------|---------|-------|------|
| `AppRoutes` | routes/index.tsx:9 | 1 (app entry) | routes/index.test.tsx ✅ | Single source of routing truth |
| `useAuth` | useAuth.ts:20 | 9 (Navbar, SupplierDashboard, Suppliers, UploadInvoice) | useAuth.test.ts ✅ | #1 frontend hub — auth context |
| `apiClient` | api/client.ts | all data-fetching pages | indirect | Axios + JWT interceptor |
| `Navbar` | Navbar.tsx:6 | 1 (AppRoutes) | ⚠️ no test | Auto-fetches /users/me on mount |
| `ApprovalDashboard` | ApprovalDashboard.tsx | 1 (AppRoutes) | ApprovalDashboard.test.tsx ✅ | Invoice list + actions |
| `UploadInvoice` | UploadInvoice.tsx:24 | 1 (AppRoutes) | ⚠️ no component test | Only MSW handlers tested |
| `Suppliers` | Suppliers.tsx:15 | 1 (AppRoutes) | ⚠️ no test | CRUD page |
| `SupplierDashboard` | SupplierDashboard.tsx:112 | 1 (AppRoutes) | SupplierDashboard.test.tsx ✅ | Recharts + KPIs |
| `KpiCard` | SupplierDashboard.tsx:341 | 1 (SupplierDashboard) | indirect | 5 instances rendered |
| `ChartCard` | SupplierDashboard.tsx:377 | 1 (SupplierDashboard) | indirect | Chart wrapper |

### Call paths through this area
```
[AppRoutes dynamic dispatch — CodeGraph verified]
AppRoutes (routes/index.tsx:9)
  → Navbar          [renders <Navbar>]
  → ApprovalDashboard  [route /dashboard]
  → UploadInvoice     [route /upload]
  → Suppliers         [route /suppliers]
  → SupplierDashboard [route /suppliers/:id/dashboard]

[Auth bootstrap]
Navbar (Navbar.tsx:6) → useEffect on mount
  → apiClient.get('/users/me')
  → login(profile, 'dev-token') → localStorage
  → useAuth populated → 9 callers can now use hasRole()

[SupplierDashboard component tree]
SupplierDashboard (SupplierDashboard.tsx:112)
  → useQuery(['supplier-stats', id]) → apiClient.get('/suppliers/{id}/stats')
  → normalizeStats (adapter: handles 3 field-name variants)
  → KpiCard × 5        [annual total, % share, avg, count, top invoice]
  → ChartCard → AreaChart (monthly) | PieChart (share + status) | BarChart (top items)
  → EmptyChart          [fallback when no data]
```

### Per-symbol test coverage
- `ApprovalDashboard`: `ApprovalDashboard.test.tsx` ✅ (sorting, empty state, approval, delete, pagination)
- `SupplierDashboard`: `SupplierDashboard.test.tsx` + `routes/index.test.tsx` ✅ (KPIs, charts, error, routing)
- `useAuth`: `useAuth.test.ts` ✅
- `AppRoutes`: `routes/index.test.tsx` ✅ (routing)
- `UploadInvoice`: ⚠️ no direct component test — only MSW handlers (`UploadInvoice.handlers.ts` → `UploadInvoice.test.tsx`)
- `Suppliers`: ⚠️ no covering test found
- `Navbar`: ⚠️ no covering test found

### Cross-layer dependencies
- **API contract:** endpoints referenced here (`/invoices`, `/invoices/upload`, `/suppliers/{id}/stats`) must match the canonical list in `invoices-api` skill. Both skills list them independently — drift risk.
- **`Invoice` TypeScript interface** (ApprovalDashboard.tsx:5) must match `InvoiceResponse` Pydantic model (schemas.py:116). The backend returns camelCase via `InvoiceResponse`; frontend consumes it directly. Any field addition/removal must sync both sides.
- **`normalizeStats` adapter** (SupplierDashboard.tsx:92) handles 3 backend field-name variants for annual total (`annualTotal` | `annualAccumulated` | `totalAmount`). This is a resilience pattern against API evolution — do not remove it without confirming the backend has stabilized on a single field name.
- **Auth-gated rendering:** `UploadInvoice` checks `hasRole('Approver') || hasRole('Admin')` — but backend allows `Clerk` too. A Clerk user would see the restricted message on the frontend even though backend authorizes them. See `invoices-auth` skill for the full drift analysis.
- **`useAuth` has 9 callers** — changing its return shape (e.g., adding a `permissions` array) requires updating all 9 call sites. This is the highest blast-radius change in the frontend.

## File Structure

```
frontend/src/
├── pages/
│   ├── ApprovalDashboard.tsx       # List, sort, filter, paginate, approve/reject
│   ├── ApprovalDashboard.test.tsx
│   ├── ApprovalDashboard.handlers.ts
│   ├── UploadInvoice.tsx           # File upload + extraction review
│   ├── UploadInvoice.test.tsx
│   ├── UploadInvoice.handlers.ts
│   ├── Suppliers.tsx               # Supplier list + search
│   ├── Suppliers.test.tsx
│   └── Suppliers.handlers.ts
├── components/
│   └── Navbar.tsx                  # Shared navigation
├── api/
│   └── client.ts                   # Axios instance with JWT interceptor
├── hooks/
│   └── useAuth.ts                  # Auth state, login, logout, hasRole
└── mocks/
    ├── handlers.ts                 # Global MSW handlers
    └── server.ts                   # MSW server setup
```
