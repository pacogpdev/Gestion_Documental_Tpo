# Tasks: Frontend Tailwind Setup

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~35 (5 files, excluding auto-generated lockfile) |
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
| 1 | Tailwind + PostCSS wiring | PR 1 (single) | `main` base; all 5 files, single commit |

## Phase 1: Foundation — Dependency Installation

- [x] 1.1 Run `npm install -D tailwindcss postcss autoprefixer` in `frontend/` — adds 3 devDependencies to `frontend/package.json`
- [x] 1.2 Verify installation: `npm ls --depth=0` shows `tailwindcss`, `postcss`, `autoprefixer` under devDependencies

## Phase 2: Configuration Files

- [x] 2.1 Create `frontend/tailwind.config.js` — CJS `module.exports` with `content: ['./src/**/*.{js,ts,jsx,tsx}']`, empty `theme.extend` and `plugins`
- [x] 2.2 Create `frontend/postcss.config.js` — CJS `module.exports` with `plugins: { tailwindcss: {}, autoprefixer: {} }`

## Phase 3: CSS Entry & App Wiring

- [x] 3.1 Create `frontend/src/index.css` — three `@tailwind` directives: `@tailwind base;`, `@tailwind components;`, `@tailwind utilities;`
- [x] 3.2 Add `import './index.css'` to `frontend/src/main.tsx` — insert after `react-dom/client` import, before `./routes` import

## Phase 4: Verification

- [x] 4.1 Run `npm run build` — verify output CSS bundle contains resolved declarations for `.bg-slate-800` and `.text-white`
- [x] 4.2 Run `npm test` — confirm no regressions from new CSS import (Vitest handles CSS automatically)
