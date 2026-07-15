# frontend-useauth-completion Specification

## Purpose

Complete the `useAuth` hook test suite with logout token cleanup and localStorage hydration scenarios. Existing tests must pass unchanged.

## Requirements

### Requirement: Logout Clears Token

`logout()` MUST clear the auth token from React state and localStorage.

#### Scenario: Logout clears state and storage

- GIVEN a logged-in user with token in state and localStorage key `auth_token`
- WHEN `logout()` is called
- THEN `user` is `null`, `token` is `null`, and `auth_token` is removed from localStorage

### Requirement: Hydration from localStorage

On mount, if a valid token exists in localStorage, the hook MUST restore the session.

#### Scenario: Valid token restores session

- GIVEN localStorage contains a valid token under `auth_token`
- WHEN the hook mounts
- THEN `user` is populated and `isAuthenticated` is `true`

#### Scenario: Expired or missing token defaults to unauthenticated

- GIVEN localStorage contains an expired token OR no `auth_token` key
- WHEN the hook mounts
- THEN `user` is `null`, `isAuthenticated` is `false`
- AND any expired token is removed from localStorage

### Requirement: Existing Tests Preserved

Existing `useAuth` tests (login, role-check, etc.) MUST continue to pass without modification.

#### Scenario: Regression-free

- GIVEN the 4 existing `useAuth` tests
- WHEN `npm test` runs
- THEN all existing tests pass with unchanged assertions
