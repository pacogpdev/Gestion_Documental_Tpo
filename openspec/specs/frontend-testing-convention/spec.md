# frontend-testing-convention Specification

## Purpose

Document and enforce the co-location testing convention for the frontend codebase. Every source file must have its test file in the same directory.

## Requirements

### Requirement: Co-located Test Files

Every source file MUST have its test file in the same directory with `.test.{ts,tsx}` extension.

| Source | Test |
|--------|------|
| `components/Foo.tsx` | `components/Foo.test.tsx` |
| `hooks/useBar.ts` | `hooks/useBar.test.ts` |

### Requirement: Test Imports from test-utils

All test files MUST import from `../test-utils` (or relative equivalent), never directly from `@testing-library/react`.

#### Scenario: Correct import path

- GIVEN `src/hooks/useBar.test.ts`
- WHEN importing `render`, `screen`, `waitFor`
- THEN the import targets `../test-utils` and no `@testing-library/react` import exists

### Requirement: MSW Handler Organization

MSW handlers for a single test stay in the test file. Shared handlers go in a co-located `{Name}.handlers.ts`.

| Scope | Location |
|-------|----------|
| Single test | `Foo.test.tsx` (inline `server.use()`) |
| Multiple tests | `Foo.handlers.ts` (imported by tests) |

### Requirement: Convention Documentation

The testing convention MUST be documented in the JSDoc header of `src/test-utils.tsx`.

#### Scenario: Convention is discoverable

- GIVEN any developer or AI agent opens `src/test-utils.tsx`
- THEN the file's JSDoc header documents co-location, import rules, and handler organization
