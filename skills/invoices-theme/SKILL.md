---
name: invoices-theme
description: >
  Tailwind CSS patterns for invoices app. Default utility classes, status colors, hover states, responsive layout.
  Trigger: When editing frontend/src/index.css, tailwind.config.js, styling components, or working with colors and design tokens.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Styling new components or modifying existing styles
- Adding colors, backgrounds, or borders
- Working with `index.css` or Tailwind configuration

## Critical Patterns

### Tailwind setup

This project uses **Tailwind CSS v3** with the standard `@tailwind` directives:

```css
/* frontend/src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

```js
// frontend/tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

### Status color convention

| Status | Background | Text |
|--------|-----------|------|
| Pending | `bg-orange-100` | `text-orange-700` |
| Approved | `bg-green-100` | `text-green-700` |
| Rejected | `bg-red-100` | `text-red-700` |

### Interactive state conventions

| State | Style |
|-------|-------|
| Button hover (approve) | `bg-green-50 hover:bg-green-100 text-green-600` |
| Button hover (reject) | `bg-red-50 hover:bg-red-100 text-red-600` |
| Button hover (delete) | `text-slate-400 hover:text-red-600 hover:bg-red-50` |
| Table row hover | `hover:bg-slate-50` |
| Card hover (unselected) | `hover:border-slate-300` |
| Card border (selected) | `border-blue-500 bg-blue-50` |

### Layout patterns

**Page container:**
```html
<div className="max-w-6xl mx-auto p-6">
```

**Summary cards grid:**
```html
<div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
  <!-- 4 cards, stacked on mobile, 4 columns on md+ -->
</div>
```

**Data table:**
```html
<div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
  <table className="w-full text-left text-sm">
    <thead className="bg-slate-50 text-slate-600 uppercase text-xs">
      <tr>
        <th className="p-4 font-semibold">Column</th>
      </tr>
    </thead>
    <tbody className="divide-y">
      <tr data-testid="invoice-row-{id}" className="hover:bg-slate-50 transition-colors">
        <td className="p-4 font-medium text-slate-800">Value</td>
        <td className="p-4 text-slate-600">Value</td>
      </tr>
    </tbody>
  </table>
</div>
```

### Card component pattern

```html
<div
  data-testid="summary-pending"
  onClick={() => setStatusFilter('Pending')}
  className="cursor-pointer p-4 rounded-lg shadow-sm border-2 transition-all border-slate-200 bg-white hover:border-slate-300"
>
  <p className="text-xs font-bold text-slate-500 uppercase">Label</p>
  <p className="text-3xl font-bold text-orange-500">42</p>
</div>
```

### Sort indicator colors

- Active direction: `text-blue-600`
- Inactive direction: `text-slate-300`

### Input/search styling

```html
<input
  data-testid="search-input"
  type="text"
  placeholder="Search invoices..."
  value={searchQuery}
  onChange={e => setSearchQuery(e.target.value)}
  className="w-full p-3 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-shadow"
/>
```

### Pagination bar

```html
<div className="flex items-center justify-between py-3 px-1 text-sm text-slate-500">
  <span>Showing <strong>1–15</strong> of <strong>42</strong> invoices</span>
  <div className="flex gap-2">
    <button disabled={page <= 1}
      className="px-3 py-1.5 rounded border border-slate-300 text-slate-600 text-xs font-semibold
        transition-colors hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed">
      ← Previous
    </button>
    <button disabled={page >= totalPages} ...>
      Next →
    </button>
  </div>
</div>
```

### Disabled state convention

Always apply both opacity and cursor change:

```html
className="... disabled:opacity-40 disabled:cursor-not-allowed"
```

## File Structure

```
frontend/
├── src/
│   └── index.css                 # Tailwind directives only (v3)
├── tailwind.config.js            # Tailwind configuration
├── postcss.config.js             # PostCSS config for Tailwind
└── package.json                  # tailwindcss + postcss dependencies
```
