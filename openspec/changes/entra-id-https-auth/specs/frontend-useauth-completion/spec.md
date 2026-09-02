# Delta for frontend-useauth-completion

## MODIFIED Requirements

### Requirement: Hydration from localStorage

On mount, the hook MUST restore only an active MSAL Entra session, acquire an API access token when required, and expose an unauthenticated state when no session or token acquisition fails. It MUST clear obsolete development-token/profile storage and logout MUST end the local session state.
(Previously: Hydrated a locally stored token and profile, including the development-token path.)

#### Scenario: Valid token restores session
- GIVEN MSAL has an active Entra account
- WHEN the hook mounts
- THEN it exposes the synchronized profile and API token for requests

#### Scenario: Expired or missing token defaults to unauthenticated
- GIVEN no active account or a failed token acquisition
- WHEN the hook mounts or refreshes
- THEN it is unauthenticated and protected UI is unavailable

## ADDED Requirements

### Requirement: MSAL Login and Logout Lifecycle

The UI MUST initiate Entra sign-in through MSAL for unauthenticated protected access, attach only the acquired API access token to API requests, and use the Entra logout lifecycle when signing out.

#### Scenario: Protected access requires sign-in
- GIVEN a user has no active Entra session
- WHEN the user opens a protected route
- THEN the UI initiates sign-in and does not call the API as authenticated

#### Scenario: Logout ends the session
- GIVEN a user has an active Entra session
- WHEN the user logs out
- THEN local authenticated state is cleared and Entra logout is invoked
