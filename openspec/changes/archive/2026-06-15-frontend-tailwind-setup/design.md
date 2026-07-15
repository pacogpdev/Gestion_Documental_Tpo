# Design: Frontend Tailwind Setup

## Technical Approach

Wire Tailwind CSS into the existing Vite build pipeline as a PostCSS plugin. No Vite plugin is needed — Vite 5 auto-detects `postcss.config.js` and processes `@tailwind` directives at build time. This is the standard Tailwind + Vite integration path, matching the proposal's approach and fulfilling all spec scenarios.

## Architecture Decisions

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **Config module: CJS (`module.exports`)** vs ESM (`export default`) | Project has no `"type": "module"` in `package.json` — `.js` files default to CJS. Vite handles both, but Tailwind docs standard is CJS. | **CJS `module.exports`** — zero-config, matches Node resolution, avoids ambiguity. |
| **Content paths: `.{ts,tsx}` only** vs `.{js,ts,jsx,tsx}` | Extra extensions are no-ops for non-existent files but future-proof. Spec uses `{ts,tsx}`, proposal uses broader set. | **`./src/** /*.{js,ts,jsx,tsx}`** — broader scan is harmless, avoids missing files if `.jsx` components are added later. |
| **CSS import placement** — before local imports vs after | Order doesn't affect Vite compilation, but conventional grouping improves readability. | **After third-party, before local modules** — natural visual separation of concerns. |

## Data Flow

```
src/**/*.tsx (Tailwind classes)
        │
        ▼
  tailwind.config.js ──→ content scanning ──→ class generation
        │
postcss.config.js ──→ tailwindcss plugin ──→ @tailwind directives resolved
        │
        └── autoprefixer plugin ──→ vendor prefixes added
        │
        ▼
  Vite build pipeline ──→ static CSS bundle with resolved utilities
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/package.json` | Modify | Add `tailwindcss`, `postcss`, `autoprefixer` as devDependencies |
| `frontend/tailwind.config.js` | Create | Tailwind configuration — content paths scanning `./src/**/*.{js,ts,jsx,tsx}` |
| `frontend/postcss.config.js` | Create | PostCSS plugin chain — `tailwindcss` + `autoprefixer` |
| `frontend/src/index.css` | Create | Global CSS entry — three `@tailwind` directives |
| `frontend/src/main.tsx` | Modify | Import `./index.css` after vendor imports, before local modules |

## Interfaces / Contracts

### tailwind.config.js

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: {} },
  plugins: [],
};
```

### postcss.config.js

```js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

### frontend/src/index.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### main.tsx import insertion point

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';              // ← inserted here
import AppRoutes from './routes';

ReactDOM.createRoot(...)
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Config files exist with correct content | Read files in CI, verify `content` array, `plugins` object, and `@tailwind` directives match expected values |
| Build | `npm run build` compiles without errors | Run `npm run build` — output CSS bundle must contain Tailwind utility declarations (e.g., `.bg-slate-800`) |
| Integration | Tests still pass with CSS import | Run `npm test` — vitest's default CSS handling treats imports as empty objects, no special config needed |

## Migration / Rollout

No migration required. This is a pure build-pipeline addition — existing components continue working, now with resolved styles.

## Open Questions

None. The design is fully constrained by the spec scenarios.
