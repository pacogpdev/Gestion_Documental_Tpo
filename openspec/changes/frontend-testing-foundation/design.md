# Design: Frontend Testing Foundation

## Technical Approach

Establish frontend testing infrastructure via MSW 2.x for API mocking, shared test utilities with provider wrapping, complete `useAuth` test coverage, and documented conventions. All new code lives under `frontend/src/`. No backend changes.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|-------------|-----------|
| MSW lifecycle | `beforeAll/afterAll/afterEach` in `setup.ts`, server instance in `server.ts` | Single file for both; globalSetup | Separation: server instantiation reusable across files, lifecycle in test setup |
| Auth injection | localStorage pre-population via `render` options | Mock `useAuth` module | `useAuth` is a standalone hook (no Context); localStorage mimics real behavior without coupling to implementation |
| Provider wrapper | `MemoryRouter` only | Full Router, BrowserRouter | Sufficient for component tests; no URL-based navigation needed |
| Convention docs | JSDoc in `test-utils.tsx` + `TESTING.md` | JSDoc only | Both inline reference AND dedicated guide for team onboarding |
| MSW package | `msw@^2` | `msw@1.x`, `nock`, `miragejs` | MSW 2.x is current; `setupServer` works with jsdom; intercepts at network level |

## Data Flow

```
Test file
  ├── render(<Component />, { user, route })
  │     ├── pre-populates localStorage (if user/token provided)
  │     └── wraps in MemoryRouter (initialEntries: [route])
  │           └── Component renders
  │                 ├── useAuth() reads localStorage
  │                 └── apiClient (axios) calls → MSW intercepts
  │
  └── server.use(http.get(...)) → per-test API stub
```

MSW sits at the network boundary — axios requests are intercepted before hitting the wire. `useAuth` hook reads from localStorage directly (no context provider).

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/package.json` | Modify | Add `msw@^2` devDependency |
| `frontend/src/mocks/server.ts` | Create | Exports `setupServer(...handlers)` instance |
| `frontend/src/mocks/handlers.ts` | Create | Shared handler: `http.get('/api/v1/users/me')` returning mock user |
| `frontend/src/test-utils.tsx` | Create | Custom `render` with MemoryRouter, localStorage auth injection, re-exports from `@testing-library/react` |
| `frontend/src/test/setup.ts` | Modify | Add MSW server lifecycle: `beforeAll(server.listen)`, `afterEach(server.resetHandlers)`, `afterAll(server.close)` |
| `frontend/vitest.config.ts` | Modify | Add `resolve.conditions: ['browser']` for MSW browser field |
| `frontend/src/hooks/useAuth.test.ts` | Modify | Add 2 tests: logout clears state+storage, localStorage hydration restores session |
| `frontend/TESTING.md` | Create | Convention reference: co-location rules, import from test-utils, handler organization, examples, anti-patterns |

## Interfaces / Contracts

### `render` function (test-utils.tsx)

```ts
interface RenderOptions {
  route?: string;       // initial MemoryRouter entry (default: '/')
  user?: { email: string; fullName: string; roles: UserRole[] } | null;
  token?: string;       // pre-populates auth_token in localStorage
}

function render(ui: ReactElement, options?: RenderOptions): RenderResult
```

`AllTheProviders` wraps with `<MemoryRouter initialEntries={[route]}>`. If `user` or `token` provided, `localStorage.setItem` is called before render.

### MSW server (src/mocks/server.ts)

```ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';
export const server = setupServer(...handlers);
```

### Handler override pattern

```ts
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';

server.use(
  http.get('/api/v1/invoices', () => HttpResponse.json([...]))
);
```

### useAuth test additions

- **Logout**: `act(() => result.current.logout())` → assert `user === null`, `auth_token` and `user_profile` removed from localStorage.
- **Hydration**: `localStorage.setItem('user_profile', JSON.stringify(mockUser))` before `renderHook` → assert `user` matches, `loading === false`.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `useAuth` logout clears state + storage | `renderHook` + `act()` |
| Unit | `useAuth` hydration from localStorage | Pre-populate storage before hook render |
| Unit | Existing 4 `useAuth` tests preserved | No modifications; verify pass |
| Smoke | MSW server starts without error | Suite startup imports server; no crash |
| Smoke | `render` from test-utils works with Router | `render(<Navbar />)` renders without error |
| Smoke | Unhandled request produces MSW warning | Call unmocked endpoint; verify console warning |

## Migration / Rollout

No migration required. All changes additive. Existing tests pass alongside new infrastructure.

## Open Questions

None.
