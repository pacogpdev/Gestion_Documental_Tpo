# Design: Frontend Dev Server

## Technical Approach

Bootstrap a Vite dev server for the existing React frontend by creating three new files (entry HTML, Vite config, React mount point), adding three npm scripts, and making one env var replacement in the API client. Zero new dependencies — `vite` and `@vitejs/plugin-react` are already installed.

## Architecture Decisions

### Decision: vite.config.ts import source

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `import { defineConfig } from 'vite'` | Standard Vite config, clean separation from test config | ✅ **Chosen** |
| `import { defineConfig } from 'vitest/config'` | Works but couples dev config to test config | Rejected — vitest.config.ts already exists for test concerns |

**Rationale**: `vite`'s own `defineConfig` is the canonical source. The existing `vitest.config.ts` uses `vitest/config` correctly for its domain; mixing them would create a circular import smell.

### Decision: StrictMode wrapping

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `<React.StrictMode><AppRoutes /></React.StrictMode>` | Catches side-effect bugs in development | ✅ **Chosen** (spec: SHOULD) |
| Unwrapped | Simpler, one less nesting level | Rejected — StrictMode is standard React 18 practice |

### Decision: Vite server options

| Option | Tradeoff | Decision |
|--------|----------|----------|
| No explicit server config | Default port 5173, host localhost | ✅ **Chosen** |
| Hardcode port/host | Matches CRA default (3000), but couples config | Rejected — no requirement to fix a port; keep defaults |

**Rationale**: The frontend has no hardcoded port references. Vite's defaults (port 5173, `localhost` host) work as-is. Adding config would be speculative.

### Decision: Env var fallback

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `import.meta.env.VITE_API_URL \|\| 'http://localhost:8000/api'` | Same fallback as current CRA code | ✅ **Chosen** (spec: SHOULD remain) |
| No fallback, require explicit env var | Breaks local dev without `.env` | Rejected — unnecessary friction |

### Decision: Script placement in package.json

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Insert after `test:ui` | Groups Vite scripts together, minimal diff | ✅ **Chosen** |
| Insert at top of scripts | More natural reading order but larger diff | Rejected — prefer minimal diff for review |

## Data Flow

```
User request (localhost:5173)
  │
  ▼
Vite Dev Server (vite.config.ts)
  │
  ├── serves index.html ──► module script ──► main.tsx
  │                                              │
  │                                              ▼
  │                                    AppRoutes (routes/index.tsx)
  │                                              │
  │                              ┌───────────────┼───────────────┐
  │                              ▼               ▼               ▼
  │                         UploadInvoice   Suppliers   ApprovalDashboard
  │                              │
  │                              ▼
  │                         apiClient (client.ts)
  │                              │
  │                              ▼
  │                         VITE_API_URL ──► Backend API
  │
  └── HMR / file watcher (dev only)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/index.html` | Create | Vite entry point: HTML5 boilerplate, `<div id="root">`, `<script type="module" src="/src/main.tsx">` |
| `frontend/vite.config.ts` | Create | Vite config: `defineConfig` from `vite`, `react()` plugin |
| `frontend/src/main.tsx` | Create | React 18 mount: `createRoot`, StrictMode, import `AppRoutes` from `./routes` |
| `frontend/package.json` | Modify | Add `dev`, `build`, `preview` scripts (after existing `test:ui`) |
| `frontend/src/api/client.ts` | Modify | Replace `process.env.REACT_APP_API_URL` → `import.meta.env.VITE_API_URL` |

## Interfaces / Contracts

```typescript
// frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import AppRoutes from './routes';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppRoutes />
  </React.StrictMode>
);
```

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
});
```

```html
<!-- frontend/index.html -->
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Invoice Approval</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

```typescript
// frontend/src/api/client.ts (line 4 — diff)
// Before:  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
// After:   baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
```

```jsonc
// frontend/package.json (scripts block — addition)
"scripts": {
  "test": "vitest",
  "test:ui": "vitest --ui",
  "dev": "vite",
  "build": "vite build",
  "preview": "vite preview"
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Scripts parse correctly | Assert `package.json` scripts block contains expected keys |
| Dev | Vite server starts | Manual: `npm run dev` → outputs `Local: http://localhost:5173` |
| Build | Production bundle | Manual: `npm run build` → `frontend/dist/` exists with assets |
| Build | Env var resolution | Manual: `VITE_API_URL=https://staging.example.com npm run build` |
| E2E | App renders and routes work | Manual: open `http://localhost:5173`, verify routes load |

## Migration / Rollout

No migration required. New files are additive. The single modified line in `client.ts` is backward-compatible (same fallback URL). Existing `npm test` continues to work unchanged.

## Open Questions

- [ ] No `tsconfig.json` exists at `frontend/`. Vite/esbuild transpiles without one, but `tsc --noEmit` type-checking will fail. Should we add a minimal `tsconfig.json` as part of this change or track it separately?
- [ ] The app uses Tailwind CSS classes (`min-h-screen bg-slate-50`, etc.) but no `tailwind.config.js` or CSS import exists. The app will render functionally but un styled. Is this tracked as a separate change?
