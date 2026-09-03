/**
 * Testing Utilities
 * 
 * Conventions:
 * 1. Co-location: Every source file MUST have its test file in the same directory.
 *    Example: `components/Foo.tsx` -> `components/Foo.test.tsx`
 * 2. Imports: All test files MUST import from this module, never directly from `@testing-library/react`.
 *    Example: `import { render, screen } from '../test-utils'`
 * 3. MSW Handlers:
 *    - Single test: Use inline `server.use()` in the test file.
 *    - Multiple tests: Use a co-located `{Name}.handlers.ts` file.
 */
import React, { ReactElement } from 'react';
import {
  render as rtlRender,
  RenderOptions,
  renderHook,
  screen,
  fireEvent,
  waitFor,
  cleanup,
  act,
  within,
} from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, type Permission, type User } from './hooks/useAuth';

interface RenderOptionsExtended extends RenderOptions {
  route?: string;
  user?: { email: string | null; fullName: string | null; roles: any[]; permissions?: Permission[] } | null;
  token?: string;
  queryClient?: QueryClient;
}

function render(
  ui: ReactElement,
  {
    route = '/',
    user = null,
    token = undefined,
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    }),
    ...options
  }: RenderOptionsExtended = {}
) {
  const all: Permission[] = ['read', 'statistics', 'upload', 'approve', 'delete', 'supplier_admin'];
  const permissions = user?.permissions ?? (user?.roles.includes('Admin') ? all : user?.roles.includes('Approver') ? ['read', 'statistics', 'upload', 'approve'] : user?.roles.includes('Clerk') ? ['read', 'upload'] : ['read', 'statistics']);
  const initialUser = user && { ...user, permissions } as User;

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <MemoryRouter initialEntries={[route]}>
          <QueryClientProvider client={queryClient}>
          <AuthProvider initialUser={initialUser ?? undefined}>{children}</AuthProvider>
        </QueryClientProvider>
      </MemoryRouter>
    );
  }

  return rtlRender(ui, { wrapper: Wrapper, ...options });
}

export {
  render,
  renderHook,
  screen,
  fireEvent,
  waitFor,
  cleanup,
  act,
  within,
};
