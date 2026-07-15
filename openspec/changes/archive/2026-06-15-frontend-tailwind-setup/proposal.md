# Proposal: Frontend Tailwind Setup

## Intent

Components already use Tailwind utility classes (`bg-slate-800`, `text-white`, `px-6`, etc.) but Tailwind is not installed or configured. The app builds but renders unstyled. This change wires Tailwind into the Vite pipeline so existing classes work.

## Scope

### In Scope
- Install `tailwindcss`, `postcss`, `autoprefixer` as dev dependencies
- Create `tailwind.config.js` with `content` paths scanning `frontend/src/**/*.{ts,tsx}`
- Create `postcss.config.js` enabling Tailwind + Autoprefixer plugins
- Create `frontend/src/index.css` with `@tailwind base; components; utilities;` directives
- Import `index.css` in `frontend/src/main.tsx`

### Out of Scope
- Modifying existing component styles or adding new ones
- Custom themes, design tokens, or Tailwind plugins (`forms`, `typography`, etc.)
- Backend or deployment configuration changes

## Capabilities

### New Capabilities
- `frontend-tailwind-css`: Base Tailwind CSS integration — PostCSS pipeline, config file, and directive entry point required to resolve existing utility classes at build time.

### Modified Capabilities
- None — existing specs (`frontend-dev-server`, etc.) remain unchanged. This is pure build-pipeline setup.

## Approach

1. `npm install -D tailwindcss postcss autoprefixer` in `frontend/`
2. Generate `tailwind.config.js` pointing `content` at `./src/**/*.{ts,tsx}`
3. Generate `postcss.config.js` with `tailwindcss` and `autoprefixer` plugins
4. Create `frontend/src/index.css` with the three `@tailwind` directives
5. Add `import './index.css'` to `frontend/src/main.tsx`

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/package.json` | Modified | Add 3 dev deps |
| `frontend/tailwind.config.js` | New | Tailwind content paths |
| `frontend/postcss.config.js` | New | PostCSS plugin chain |
| `frontend/src/index.css` | New | Tailwind directives entry |
| `frontend/src/main.tsx` | Modified | Import CSS file |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| CSS import breaks Vite build if PostCSS missing | Low | `postcss.config.js` is created before final build check |
| Existing test mocks break on unexpected CSS import | Low | Vitest handles CSS imports via `css: true` or identity mock |

## Rollback Plan

- `git revert` the commit
- `npm uninstall tailwindcss postcss autoprefixer`
- Remove `import './index.css'` from `main.tsx`

## Dependencies

- Node.js + npm (already present per `frontend/package.json`)
- Vite 5 (already configured, PostCSS auto-detected via config file)

## Success Criteria

- [ ] `npm run dev` produces no Tailwind-related warnings
- [ ] Existing components render with Tailwind styles (dark backgrounds, white text)
- [ ] `npm test` passes without regressions
- [ ] PostCSS config is auto-detected by Vite (no Vite plugin needed)
