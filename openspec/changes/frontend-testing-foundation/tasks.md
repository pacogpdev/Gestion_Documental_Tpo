# Tasks: Frontend Testing Foundation

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~160 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | MSW infra + vitest config + test-utils + useAuth tests + docs | PR 1 | Under 400 lines; single PR is fine |

## Phase 1: MSW Infrastructure

- [ ] 1.1 Install `msw@^2` as devDependency in `frontend/package.json`
- [ ] 1.2 Create `frontend/src/mocks/handlers.ts` — export `http.get('/api/v1/users/me')` returning mock user
- [ ] 1.3 Create `frontend/src/mocks/server.ts` — export `setupServer(...handlers)` instance
- [ ] 1.4 Update `frontend/vitest.config.ts` — add `resolve.conditions: ['browser']` for MSW browser field
- [ ] 1.5 Update `frontend/src/test/setup.ts` — add `beforeAll(server.listen)`, `afterEach(server.resetHandlers)`, `afterAll(server.close)`

## Phase 2: Test Utilities

- [ ] 2.1 Create `frontend/src/test-utils.tsx` — custom `render` wrapping `MemoryRouter`, localStorage auth injection, re-export `@testing-library/react`
- [ ] 2.2 Add JSDoc header to `test-utils.tsx` — document co-location, import, and handler organization conventions

## Phase 3: useAuth Test Completion

- [ ] 3.1 Add `logout` test to `frontend/src/hooks/useAuth.test.ts` — verify `user: null`, `auth_token` and `user_profile` removed from localStorage
- [ ] 3.2 Add localStorage hydration test — pre-populate `user_profile`, verify `user` restored and `loading: false` on mount
- [ ] 3.3 Verify all 6 tests pass with `npm test` (4 existing + 2 new)

## Phase 4: Documentation

- [ ] 4.1 Create `frontend/TESTING.md` — conventions: co-location, import from test-utils, MSW handler organization, smoke test pattern, anti-patterns
- [ ] 4.2 Run `npm test` — confirm full suite passes with MSW running
