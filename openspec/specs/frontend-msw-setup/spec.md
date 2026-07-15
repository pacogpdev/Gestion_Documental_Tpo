# frontend-msw-setup Specification

## Purpose

MSW 2.x integration for Vitest. All API-dependent frontend tests MUST use MSW to intercept requests, ensuring deterministic, network-independent test execution.

## Requirements

### Requirement: MSW Server Lifecycle

The test environment MUST start and stop an MSW server per suite via `setupServer()`.

#### Scenario: Server starts and stops per suite

- GIVEN a test file importing the MSW server
- WHEN Vitest runs the suite
- THEN `setupServer()` is called in `beforeAll` and `server.close()` in `afterAll`
- AND handlers reset via `server.resetHandlers()` in `afterEach`

### Requirement: Per-Test Handler Overrides

Individual tests MAY override handlers to simulate specific API responses.

#### Scenario: Mock success, error, and delayed response

- GIVEN a test calling `server.use()` with custom handlers
- WHEN the component makes the matching API request
- THEN the mocked `HttpResponse.json()` / `HttpResponse.error()` / `delay()` result is returned
- AND the component renders the correct success, error, or loading state

### Requirement: Network Isolation

No real network calls MUST escape during test execution.

#### Scenario: Unhandled request is caught

- GIVEN MSW handlers are active
- WHEN a component makes a request to an unhandled endpoint
- THEN MSW logs a warning AND the request never reaches the real network

### Requirement: Shared Server Module

The MSW server instance MUST live in `src/mocks/server.ts` for reuse across test files.

#### Scenario: Shared server import

- GIVEN any test file in the frontend
- WHEN it imports `{ server }` from `src/mocks/server.ts`
- THEN the same server instance is shared, with handler state isolated per suite
