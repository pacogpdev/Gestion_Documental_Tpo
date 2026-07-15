# Frontend Dev Server Specification

## Purpose

Define the Vite development server bootstrap layer — entry point, build configuration, React mount point, dev scripts, and Vite-compatible environment variable convention — required to serve the existing frontend application as a runnable web app.

## Requirements

### Requirement: Frontend Vite Bootstrap

The system MUST provide a valid Vite dev server entry point at `frontend/index.html`, a Vite configuration at `frontend/vite.config.ts`, and a React mount point at `frontend/src/main.tsx`.

#### Scenario: Index.html serves as Vite entry point

- GIVEN the `frontend/` directory
- WHEN a developer opens `frontend/index.html`
- THEN it MUST contain a `<div id="root"></div>` element
- AND a `<script type="module" src="/src/main.tsx"></script>` tag
- AND a standard HTML5 DOCTYPE and `<meta charset="UTF-8">`

#### Scenario: Vite config enables React JSX transform

- GIVEN `frontend/vite.config.ts`
- WHEN Vite loads the config
- THEN it MUST import `@vitejs/plugin-react` and call `react()` inside the `plugins` array

#### Scenario: Main.tsx renders AppRoutes via createRoot

- GIVEN `frontend/src/main.tsx`
- WHEN the module executes
- THEN it MUST import `AppRoutes` from `./routes`
- AND call `ReactDOM.createRoot(document.getElementById('root')!).render(<AppRoutes />)`
- AND SHOULD wrap `<AppRoutes />` in `<React.StrictMode>`

### Requirement: Frontend Env Config

The system MUST use Vite's `import.meta.env.VITE_*` convention for API URL configuration instead of the CRA `process.env.REACT_APP_*` convention.

#### Scenario: Client.ts uses Vite env var

- GIVEN `frontend/src/api/client.ts`
- WHEN `baseURL` is constructed
- THEN it MUST use `import.meta.env.VITE_API_URL`
- AND MUST NOT contain `process.env.REACT_APP_API_URL`
- AND the fallback SHOULD remain `'http://localhost:8000/api'`

#### Scenario: App resolves API URL from environment

- GIVEN a `.env` file with `VITE_API_URL=https://api.example.com`
- WHEN the app boots and `client.ts` initializes
- THEN `apiClient.defaults.baseURL` MUST resolve to the value of `VITE_API_URL`
- AND all API requests MUST target that URL

### Requirement: Frontend Package Scripts

The system MUST provide `dev`, `build`, and `preview` scripts in `frontend/package.json` that delegate to the Vite CLI.

#### Scenario: Dev script launches Vite server

- GIVEN `frontend/package.json`
- WHEN a developer runs `npm run dev`
- THEN it MUST execute the `vite` command
- AND start the Vite dev server (default port 5173)

#### Scenario: Build script produces production bundle

- GIVEN `frontend/package.json`
- WHEN a developer runs `npm run build`
- THEN it MUST execute `vite build`
- AND produce output in `frontend/dist/`

#### Scenario: Preview script serves production build

- GIVEN `frontend/package.json`
- WHEN a developer runs `npm run preview`
- THEN it MUST execute `vite preview`
- AND serve the `frontend/dist/` directory statically
