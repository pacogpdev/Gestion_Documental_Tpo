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

interface RenderOptionsExtended extends RenderOptions {
  route?: string;
  user?: { email: string; fullName: string; roles: any[] } | null;
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
  // Auth injection: pre-populate localStorage
  if (token) {
    localStorage.setItem('auth_token', token);
  }
  if (user) {
    localStorage.setItem('user_profile', JSON.stringify(user));
  } else if (user === null && token === undefined) {
    // If explicitly null and no token, ensure storage is clear for unauthenticated state
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_profile');
  }

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <MemoryRouter initialEntries={[route]}>
        <QueryClientProvider client={queryClient}>
          {children}
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
