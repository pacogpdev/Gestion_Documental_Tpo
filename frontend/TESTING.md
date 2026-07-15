# Frontend Testing Strategy

## Overview

This project uses **Vitest** with **React Testing Library** and **MSW (Mock Service Worker)** for integration testing of page components. Tests are co-located with the components they verify.

## Test Stack

| Tool | Purpose |
|------|---------|
| **Vitest** | Test runner (fast, Vite-native) |
| **@testing-library/react** | Component rendering, DOM queries, user interactions |
| **@testing-library/jest-dom** | Custom DOM matchers (`toBeInTheDocument`, `toHaveTextContent`, etc.) |
| **MSW** (Mock Service Worker) | Network-layer mocking for API calls |
| **jsdom** | Browser-like environment for tests |

## Running Tests

```bash
cd frontend

# Run all tests once
npm test

# Run in watch mode
npm test -- --watch

# Run a single test file
npm test -- src/pages/ApprovalDashboard.test.tsx

# Run tests matching a pattern
npm test -- -t "ApprovalDashboard"
```

## Test Architecture

### Test Setup (`src/test/setup.ts`)

- MSW server starts before all tests (`beforeAll`)
- Handlers are reset after each test (`afterEach`) to isolate test cases
- Server closes after all tests (`afterAll`)

### Shared Utilities (`src/test-utils.tsx`)

All test files **MUST** import from `../test-utils` instead of `@testing-library/react` directly. This ensures:

- `localStorage` is pre-populated with auth state (user + token)
- Components render inside a `MemoryRouter` for route-awareness
- The custom `render` function handles auth injection (role-based access tests)

```tsx
// ✅ Correct import
import { render, screen, fireEvent, waitFor } from '../test-utils';

// ❌ Never import directly
import { render, screen } from '@testing-library/react';
```

### MSW Mocking Strategy

#### Default Handlers (`src/mocks/handlers.ts`)

A global set of handlers loaded on server start. Currently includes the `/api/v1/users/me` endpoint used for auth.

#### Per-Suite Handlers (co-located `*.handlers.ts`)

For page-specific API endpoints, create a co-located handlers file:

```
src/pages/
├── UploadInvoice.tsx
├── UploadInvoice.handlers.ts       # Mock responses for UploadInvoice API
├── UploadInvoice.test.tsx
├── ApprovalDashboard.tsx
├── ApprovalDashboard.handlers.ts   # Mock responses for ApprovalDashboard API
├── ApprovalDashboard.test.tsx
├── Suppliers.tsx
├── Suppliers.handlers.ts           # Mock responses for Suppliers API
└── Suppliers.test.tsx
```

#### Test-Level Overrides (inline `server.use()`)

For edge cases or tests that need different data, use `server.use()` directly in the test file:

```tsx
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';

it('handles empty state', async () => {
  server.use(
    http.get('http://localhost:8000/api/invoices', () => {
      return HttpResponse.json([]);
    })
  );
  // ... test assertions
});
```

### MSW URL Format

Handlers loaded via `server.use()` require **full URLs**:

```tsx
// ✅ When used with server.use()
http.get('http://localhost:8000/api/invoices', handler)
http.patch('http://localhost:8000/api/invoices/:id/approve', handler)
```

Default handlers passed to `setupServer()` can use relative paths:

```ts
// ✅ When loaded into setupServer() 
http.get('/api/v1/users/me', handler)
```

## Adding a New Page Test

Follow this checklist to add integration tests for a new page:

### 1. Create handlers file (`{Page}.handlers.ts`)

```ts
import { http, HttpResponse } from 'msw';

export const mockData = [ /* ... */ ];

export const pageHandlers = [
  http.get('http://localhost:8000/api/page-endpoint', () => {
    return HttpResponse.json(mockData);
  }),
];
```

### 2. Create test file (`{Page}.test.tsx`)

```tsx
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../test-utils';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';
import PageComponent from './PageComponent';
import { pageHandlers } from './PageComponent.handlers';

describe('PageComponent', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  // Happy path: component renders with data
  it('renders data from API on mount', async () => {
    server.use(...pageHandlers);
    render(<PageComponent />, { user: ..., token: '...', route: '...' });

    await waitFor(() => {
      expect(screen.getByText('Expected Data')).toBeInTheDocument();
    });
  });

  // Role access: test different user roles
  it('hides admin feature for non-admin roles', async () => {
    render(<PageComponent />, { user: { ..., roles: ['Viewer'] }, ... });
    expect(screen.queryByTestId('admin-button')).not.toBeInTheDocument();
  });

  // Empty state
  it('shows empty state when API returns no data', async () => {
    server.use(http.get('...', () => HttpResponse.json([])));
    render(<PageComponent />, ...);
    await waitFor(() => {
      expect(screen.getByText('No items found.')).toBeInTheDocument();
    });
  });

  // Error state
  it('handles API errors gracefully', async () => {
    server.use(http.get('...', () => new HttpResponse(null, { status: 500 })));
    render(<PageComponent />, ...);
    // Assert user-friendly error feedback
  });
});
```

### 3. Common Test Patterns

| Pattern | Technique |
|---------|-----------|
| **Data loading** | Use a delayed handler (`await new Promise(r => setTimeout(r, 50))`) to capture the loading state |
| **Empty state** | Return `[]` from the handler |
| **Role-based access** | Pass different `user` objects with `roles: ['Admin'|'Viewer'|'Approver']` |
| **Dynamic filtering** | Use `fireEvent.change()` on a text input and assert visible/filtered-out items |
| **Action → refresh** | Assert action (PATCH/POST) was called via a flag variable, then verify list re-renders |
| **Error handling** | Return error status from MSW handler; verify `alert()` or error message display |

### 4. Run and Verify

```bash
cd frontend
npm test
```

All tests must pass. No `console.log` or debug artifacts should remain in test files.

## Current Test Coverage

| Page | Test File | Tests | Coverage |
|------|-----------|-------|----------|
| UploadInvoice | `UploadInvoice.test.tsx` | 4 | Happy path, API error, validation, role access |
| ApprovalDashboard | `ApprovalDashboard.test.tsx` | 4 | Loading state, empty state, approve, reject |
| Suppliers | `Suppliers.test.tsx` | 6 | List rendering, role access (3 roles), search/filter (2) |
| useAuth (hook) | `useAuth.test.ts` | 6 | Login, logout, hasRole, hydration, edge cases |
| apiClient | `client.test.ts` | 2 | Base URL config |

**Total:** 22 tests across 5 test files.
