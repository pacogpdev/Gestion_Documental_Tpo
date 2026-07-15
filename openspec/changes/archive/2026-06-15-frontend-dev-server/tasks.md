# Tasks: Frontend Dev Server

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~35 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Phase 1: Vite Entry & Config

- [x] 1.1 Create `frontend/index.html` — HTML5 template with `<div id="root">` and `<script type="module" src="/src/main.tsx">`
- [x] 1.2 Create `frontend/vite.config.ts` — import `defineConfig` from `vite` and `react` from `@vitejs/plugin-react`, export with `plugins: [react()]`

## Phase 2: React Mount & Scripts

- [x] 2.1 Create `frontend/src/main.tsx` — import `React`, `ReactDOM`, `AppRoutes` from `./routes`, render via `createRoot` inside `<React.StrictMode>`
- [x] 2.2 Update `frontend/package.json` — add `dev: "vite"`, `build: "vite build"`, `preview: "vite preview"` scripts after `test:ui`

## Phase 3: Env Var Convention

- [x] 3.1 Modify `frontend/src/api/client.ts` — replace `process.env.REACT_APP_API_URL` with `import.meta.env.VITE_API_URL` (preserve same fallback)

## Phase 4: Verification

- [ ] 4.1 Run `npm run dev` — confirm Vite dev server starts at `http://localhost:5173`
- [ ] 4.2 Run `npm run build` — confirm `frontend/dist/` is produced with assets
- [x] 4.3 Run `npm test` — confirm existing Vitest tests still pass
