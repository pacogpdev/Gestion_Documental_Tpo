# Frontend Tailwind CSS Specification

## Purpose

Integrate Tailwind CSS into the Vite build pipeline so existing utility classes (`bg-slate-800`, `text-white`, `px-6`, etc.) resolve correctly at build time.

## ADDED Requirements

This is a new capability — no prior spec existed for this domain.

### Requirement: Tailwind Config Setup

The project MUST install `tailwindcss`, `postcss`, and `autoprefixer` as devDependencies in `frontend/package.json`. A `tailwind.config.js` SHALL exist with `content` paths scanning `./src/**/*.{ts,tsx}`. A `postcss.config.js` SHALL exist with `tailwindcss` and `autoprefixer` plugins enabled.

#### Scenario: Dev dependencies are installed

- GIVEN the `frontend/` directory
- WHEN `npm ls --depth=0` is run
- THEN `tailwindcss`, `postcss`, and `autoprefixer` MUST appear under devDependencies

#### Scenario: Tailwind config scans source files

- GIVEN `frontend/tailwind.config.js`
- WHEN its `content` array is inspected
- THEN it MUST include `./src/**/*.{ts,tsx}`

#### Scenario: PostCSS plugins are enabled

- GIVEN `frontend/postcss.config.js`
- WHEN its `plugins` list is read
- THEN it MUST include both `tailwindcss` and `autoprefixer`

#### Scenario: Build resolves Tailwind utilities

- GIVEN a component using `className="bg-slate-800 text-white"`
- WHEN `npm run build` executes
- THEN the output CSS bundle MUST contain the resolved utility declarations for `bg-slate-800` and `text-white`

### Requirement: CSS Entry Point

A global CSS entry file SHALL exist at `frontend/src/index.css` containing the three `@tailwind` directives. This file MUST be imported at the top of `frontend/src/main.tsx` before any other local imports.

#### Scenario: Directive file is present

- GIVEN `frontend/src/index.css`
- WHEN the file is read
- THEN it MUST contain `@tailwind base;`, `@tailwind components;`, and `@tailwind utilities;`

#### Scenario: CSS import in entry point

- GIVEN `frontend/src/main.tsx`
- WHEN the file is read
- THEN an `import './index.css'` MUST appear at the top, before any component or route imports

#### Scenario: Tailwind styles render globally

- GIVEN the application is built with `npm run build`
- WHEN the output is served and viewed in a browser
- THEN elements using Tailwind utility classes MUST display with the expected computed styles (e.g., `bg-slate-800` renders as `rgb(30 41 59)`)
