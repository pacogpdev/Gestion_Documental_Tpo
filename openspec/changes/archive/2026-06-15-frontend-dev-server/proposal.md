# Proposal: Frontend Dev Server

## Intent

The frontend has full source code (pages, components, hooks, API client, routes) and testing infrastructure, but cannot be served as a web app. It lacks the Vite bootstrap layer: `index.html`, `vite.config.ts`, `src/main.tsx`, dev/build scripts, and uses a CRA env var convention (`process.env.REACT_APP_API_URL`) incompatible with Vite (`import.meta.env.VITE_*`). This change bridges that gap with zero logic modifications.

## Scope

### In Scope
- Create `frontend/index.html` — Vite entry template with root div and script tag
- Create `frontend/vite.config.ts` — Vite config with `@vitejs/plugin-react`
- Create `frontend/src/main.tsx` — renders `AppRoutes` via `ReactDOM.createRoot`
- Update `frontend/package.json` — add `dev`, `build`, `preview` scripts
- Fix `frontend/src/api/client.ts` — replace `process.env.REACT_APP_API_URL` with `import.meta.env.VITE_API_URL`

### Out of Scope
- Page/component logic changes
- Styling or CSS configuration (Tailwind, etc.)
- Backend changes
- `vite-env.d.ts` (included only if needed for type-checking)

## Capabilities

> Researched `openspec/specs/` — existing frontend specs cover testing convention, test-utils, MSW setup, and useAuth completion. No dev-server spec exists.

### New Capabilities
- `frontend-dev-server`: Vite dev server bootstrap — HTML entry point, Vite configuration, React mount point, dev/build scripts, and Vite-compatible env var convention

### Modified Capabilities
None

## Approach

1. **index.html**: Standard Vite HTML5 template with `<div id="root">` and `<script type="module" src="/src/main.tsx">`
2. **vite.config.ts**: Import `@vitejs/plugin-react`, configure with `react()` plugin. No additional plugins needed.
3. **main.tsx**: Import `StrictMode`, `AppRoutes` from `./routes`, render via `createRoot`. Wrap in `StrictMode`.
4. **package.json**: Insert three scripts (`dev → vite`, `build → vite build`, `preview → vite preview`) preserving existing `test` and `test:ui` scripts.
5. **client.ts**: One-line change — `process.env.REACT_APP_API_URL` to `import.meta.env.VITE_API_URL`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/index.html` | New | Vite entry HTML |
| `frontend/vite.config.ts` | New | Vite + React plugin config |
| `frontend/src/main.tsx` | New | React DOM mount point |
| `frontend/package.json` | Modified | Scripts section — add dev/build/preview |
| `frontend/src/api/client.ts` | Modified | CRA → Vite env var convention |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `@vitejs/plugin-react` missing | Low | Already present in `devDependencies` |
| Routes import path mismatch | Low | Verify `./routes` default export at dev start |
| Existing tests break | Low | No runtime logic changed; Vitest config unaffected |

## Rollback Plan

Git revert the commit range. If manual: delete `index.html`, `vite.config.ts`, `main.tsx`; revert `package.json` scripts and `client.ts` line to previous state.

## Dependencies

- `@vitejs/plugin-react` ^4.2.1 — already installed
- `vite` ^5.0.11 — already installed
- `react-dom` ^18.2.0 — already installed

## Success Criteria

- [ ] `npm run dev` starts the Vite dev server without errors
- [ ] `npm run build` produces a production build in `frontend/dist/`
- [ ] App renders at `http://localhost:5173` with all routes functional
- [ ] `client.ts` uses `import.meta.env.VITE_API_URL` with zero `process.env` references
