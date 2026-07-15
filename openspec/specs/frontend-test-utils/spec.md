# frontend-test-utils Specification

## Purpose

A shared `src/test-utils.tsx` module providing a custom `render` that wraps components with AuthContext and React Router MemoryRouter, eliminating per-test boilerplate.

## Requirements

### Requirement: Custom Render with Provider Wrapping

`render()` from `test-utils` MUST wrap components with AuthContext and MemoryRouter.

#### Scenario: Component renders with routing and auth context

- GIVEN a component using `useNavigate()`, `<Link>`, or `useAuth()`
- WHEN a test calls `render(<Component />)`
- THEN MemoryRouter provides routing isolation AND AuthContext provides default unauthenticated state

#### Scenario: Custom route and auth state

- GIVEN `render(<Component />, { route: '/invoices/42', user: mockUser })`
- WHEN the component mounts
- THEN `window.location.pathname` is `/invoices/42` and `useAuth()` returns `mockUser`

### Requirement: Re-export Testing Library

`test-utils` MUST re-export all `@testing-library/react` utilities.

#### Scenario: Single import source

- GIVEN a test file
- WHEN it writes `import { render, screen, fireEvent, waitFor } from '../test-utils'`
- THEN all four utilities are available without importing `@testing-library/react`

### Requirement: Minimal Boilerplate

A component test MUST render with full context in 3 lines or fewer.

#### Scenario: Three-line render

- GIVEN `<Greeting name="World" />`
- WHEN the test imports `render` from `test-utils` and calls `render(<Greeting name="World" />)`
- THEN import + render + assert fits in 3 lines
