# Proposal: Frontend Testing Foundation

## Intent

Frontend TDD maturity is 2/10. The only test (`useAuth`) is incomplete — missing `logout` and localStorage hydration scenarios. MSW is absent, blocking API-dependent tests. No shared test utilities or documented conventions exist. This change establishes the foundation so page-level tests (next change) have infrastructure, patterns, and conventions to build on.

## Scope

### In Scope
- Install and configure `msw` for Vitest API mocking
- Create `src/test-utils.tsx` with custom render wrapping AuthContext + Router providers
- Complete `useAuth.test.ts`: add `logout` scenario + localStorage hydration test
- Update `vitest.config.ts` to exclude MSW handlers from transform
- Document testing conventions in `src/test-utils.tsx` (inline doc block)

### Out of Scope
- Page tests (ApprovalDashboard, UploadInvoice, Suppliers)
- Component tests (Navbar)
- E2E tests
- Backend changes
- `useAuth.test.ts` co-location migration — **already co-located** at `src/hooks/`

## Capabilities

> Researched `openspec/specs/` — no frontend testing specs exist. All existing specs are backend-focused.

### New Capabilities
- `frontend-test-infrastructure`: MSW setup, shared test utilities with provider wrappers, co-location convention, and testing documentation

### Modified Capabilities
None — no existing frontend specs to modify.

## Approach

1. **MSW**: Install `msw`, create `src/mocks/handlers.ts` + `src/mocks/server.ts`, wire into Vitest via `setupFiles` or `vi.mock` + `beforeAll`/`afterAll` in setup.
2. **Test utils**: `src/test-utils.tsx` exports `render` wrapping `MemoryRouter` + a minimal `AuthProvider` (or direct `useAuth` injection). Pattern: `render(ui, { route?, user? })`.
3. **useAuth completion**: Two new tests in existing file — logout clears localStorage + user becomes null; localStorage hydration restores user on mount.
4. **Convention doc**: Inline JSDoc block at top of `test-utils.tsx` documenting co-location rule, naming, and provider wrapping pattern. No separate `TESTING.md` — single source of truth in the utils file.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/package.json` | Modified | Add `msw` devDependency |
| `frontend/vitest.config.ts` | Modified | MSW setup integration |
| `frontend/src/test/setup.ts` | Modified | MSW server lifecycle |
| `frontend/src/test-utils.tsx` | New | Custom render + provider wrapper |
| `frontend/src/mocks/handlers.ts` | New | API handler stubs |
| `frontend/src/mocks/server.ts` | New | MSW server for Vitest |
| `frontend/src/hooks/useAuth.test.ts` | Modified | Add logout + hydration tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| MSW + jsdom compat issues | Low | MSW 2.x supports jsdom via `setupServer`; Vitest setup is documented |
| Existing test breaks on refactor | Low | Only adding tests; existing 4 pass untouched |

## Rollback Plan

Remove `msw` from `package.json`, revert `vitest.config.ts` and `setup.ts` changes, delete `src/test-utils.tsx` and `src/mocks/`. Git revert on the commit range.

## Dependencies

- None external. Vitest + Testing Library already installed.

## Success Criteria

- [ ] `npm test` passes with all 6+ `useAuth` tests (existing 4 + logout + hydration)
- [ ] MSW installed and server starts in Vitest without errors
- [ ] `render` from `test-utils.tsx` renders a component requiring Router context
- [ ] Convention documentation exists at top of `test-utils.tsx`