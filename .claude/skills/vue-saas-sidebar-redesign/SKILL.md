---
name: vue-saas-sidebar-redesign
description: Redesign a Vue 3 + vue-router application's UI into a modern SaaS-style shell - a vertical left sidebar instead of a top nav bar, a slim topbar, design tokens for consistent spacing, and a polished professional look. Use when asked to redesign or modernize a Vue layout, move navigation to a sidebar, make the app "look like a SaaS dashboard", or clean up inconsistent spacing and styling across views.
---

# Vue 3 SaaS Sidebar Redesign

Turn a top-nav Vue 3 app into a sidebar-driven SaaS shell without changing what the app does. The redesign is purely presentational: routes, API calls, state and business logic stay exactly as they are.

Reference files in this skill:
- `reference/tokens.css` - design token template (spacing, radii, shadows, colors, layout sizes)
- `reference/AppSidebar.example.vue` - a complete sidebar component (expand / collapse / mobile drawer, active state, a11y)
- `reference/example-inventory-app.md` - worked example mapping this workflow onto this repo

## Workflow

### 1. Discover (read before writing anything)
- **Routes:** read the router setup (`src/main.js`, `src/router/index.js` or similar). List every route path, its component, and any `meta` (title, icon).
- **Current shell:** read `App.vue` (or the root layout). Identify the nav markup, logo/brand, and every header widget (profile menu, language switcher, search, notifications).
- **Bars under the nav:** filter bars, toolbars, breadcrumbs. Decide whether each belongs in the topbar or as a sticky bar at the top of the content area.
- **Styles:** find the global stylesheet (often an unscoped `<style>` in `App.vue` or `src/assets/*.css`). Record the existing palette, font stack, and shared classes (`.card`, `.badge`, `.table-container`, `.page-header`, ...).
- **i18n:** if labels come from a translation helper (`t('nav.x')`), keep using it. Note any hard-coded labels that should get keys.
- **Project rules:** check CLAUDE.md / contributing docs for design-system rules (colors, "no emojis", component conventions, mandatory subagents).

Write down a short inventory (routes, widgets, shared classes, palette) before moving on.

### 2. Design tokens
Copy `reference/tokens.css` into the global stylesheet's `:root` and adapt it:
- **Derive colors from the existing palette.** Map the app's current text, muted, border, background and accent colors onto the tokens. Never invent a new brand color.
- Spacing on a 4px scale (`--space-1` = 4px ... `--space-10` = 40px). Use only these values for padding, margins and gaps.
- Radii (`--radius-sm/md/lg`), shadows (`--shadow-sm/md`), and layout sizes (`--sidebar-width`, `--sidebar-width-collapsed`, `--topbar-height`).
- Only add a dark theme if the app already has one or the user asks.

### 3. Layout shell
Replace the top nav with a CSS Grid shell:

```html
<div class="app-shell" :class="{ 'is-collapsed': collapsed, 'drawer-open': drawerOpen }">
  <AppSidebar ... />
  <div class="app-main">
    <AppTopbar ... />          <!-- page title + existing widgets -->
    <!-- optional sticky filter/toolbar bar -->
    <main class="app-content"><router-view /></main>
  </div>
</div>
```

```css
.app-shell { display: grid; grid-template-columns: var(--sidebar-width) minmax(0, 1fr); min-height: 100vh; }
.app-shell.is-collapsed { grid-template-columns: var(--sidebar-width-collapsed) minmax(0, 1fr); }
.app-main { display: flex; flex-direction: column; min-width: 0; }
.app-content { padding: var(--space-6) var(--space-8); max-width: var(--content-max-width); width: 100%; }
```

- **Sidebar:** brand at the top, nav items (inline SVG icon + label), a collapse toggle, and a footer area (user/profile or version). Sticky, full height, scrolls independently.
- **Topbar:** slim (`--topbar-height`), shows the current page title (from route `meta.title` or the matching nav label) on the left and the existing widgets on the right. Includes the mobile hamburger.
- `minmax(0, 1fr)` and `min-width: 0` are required so wide tables/charts don't blow out the grid.

### 4. Extract components
- `src/components/layout/AppSidebar.vue` - start from `reference/AppSidebar.example.vue`. Drive items from a single `navItems` array (path, label key, icon). Use `router-link`'s built-in `active-class` / `exact-active-class`; use `exact` matching for `/` so Home isn't always active.
- `src/components/layout/AppTopbar.vue` - title, hamburger (emits `toggle-drawer`), and a slot or direct use of existing widgets.
- Move existing widgets (profile menu, language switcher, filter bar) into these components **unchanged**: same props, same emits, same composables. Re-wire their events up to `App.vue` if modals live there.
- Keep `App.vue` as the owner of shell state (`collapsed`, `drawerOpen`) and any app-level modals.

### 5. Responsive behaviour
- **>= 1024px:** expanded sidebar by default; user can collapse to icons.
- **768-1023px:** collapsed to icons by default (labels shown via `title` / tooltip).
- **< 768px:** pick one phone mode. Ask the user if they haven't said.
  - **Drawer (default):** the sidebar becomes an off-canvas drawer (`position: fixed; transform: translateX(-100%)`), opened by the topbar hamburger, with a backdrop. Close it on route change, backdrop click and `Escape`. It gives full-width content and full labels, but needs a tap to navigate.
  - **Icon rail:** the sidebar stays in the grid as a `--sidebar-width-collapsed` icons-only rail, with no hamburger, backdrop or drawer state. Hide the collapse toggle on phones. Force icons-only with a media query or a computed `effectiveCollapsed`, never by writing to the saved desktop preference. Navigation is one tap, but content loses about 68px, so tighten the content padding and recheck the topbar fits.
- Persist the user's collapse choice in `localStorage`, always wrapped in `try/catch` so private mode doesn't break the app.
- **The content area just got narrower by the sidebar width.** Anything that used to fit the full viewport may now overflow:
  - Toolbars and filter bars built as non-wrapping flex rows need `flex-wrap: wrap` and shrinkable controls (`min-width: 0; flex: 1 1 140px`).
  - Multi-column view grids written as `repeat(2, 1fr)` or `1fr 1fr` need `minmax(0, 1fr)`, plus a single-column fallback at narrow widths. Plain `1fr` won't shrink below its content's width.
  - Other usual suspects in views:
    - Fixed-width inputs, such as a `min-width: 300px` search box. Use `flex: 1 1 200px; min-width: 0; max-width: ...`.
    - Card headers and chart legends that don't wrap.
    - Bar charts with many fixed-width bars. Make their container `overflow-x: auto` and give the chart a `min-width`.
    - View-specific table wrappers that don't use the shared scrolling `.table-container` class.
  - Check `document.documentElement.scrollWidth <= innerWidth` on every route. On mobile, overflow also stretches the layout viewport, which makes a fixed drawer look shifted or clipped.
- **Mobile topbar:** at 375px only the hamburger, an ellipsized title and compact widgets fit. Hide text labels inside the profile and language widgets, keeping the avatar and icon. Prefer `:deep()` from the topbar over editing those widgets.
- **Drawer focus (drawer mode only):** on open, focus the first nav item. On close, return focus to the hamburger. Set `inert` on the main area while the drawer is open. Give the hamburger `aria-controls` and `aria-expanded`.
- **Backdrop:** keep it rendered and toggle `opacity` with `pointer-events`. Switching `display` cancels the fade-in.

### 6. Polish pass (consistency across every view)
- Migrate shared classes to tokens: cards (border + `--shadow-sm` + `--radius-lg`, padding `--space-5/6`), tables (sticky header, `--color-surface-subtle` header row, row hover, consistent cell padding), badges (pill radius, tinted backgrounds), page headers (title + subtitle spacing), stat/KPI cards.
- Unify vertical rhythm: one gap value between page sections (e.g. `--space-6`), one inside cards.
- Typography: one font stack, a small type scale (12 / 13 / 14 / 16 / 20 / 24px), `font-variant-numeric: tabular-nums` for numbers in tables and KPIs.
- Replace hard-coded hex values and pixel spacing in views with tokens **only where it's a straight swap**. Don't restructure view templates.
- Accessibility: `<nav aria-label="Main">`, `aria-current="page"` on the active link (router-link does this), visible `:focus-visible` rings, buttons are `<button>`, hit targets >= 36px, sufficient contrast.
- Motion: short transitions (150-200ms) on width/transform; disable under `@media (prefers-reduced-motion: reduce)`.

### 7. Guardrails
- Do **not** change routes, API calls, data fetching, computed logic, or component props/emits contracts.
- Keep all i18n keys; add new keys for any label you newly translate (in every locale file). This includes accessible names you introduce ("Open navigation", "Collapse sidebar", the nav `aria-label`).
- Align secondary bars (filters, toolbars) with the content: same `max-width` and horizontal padding tokens, so left edges line up.
- Icons: inline SVG (stroke-based, 20px, `currentColor`). No new icon or UI dependencies unless the project already uses one.
- Follow project rules (e.g. design-system colors, "no emojis in UI", mandatory subagents for `.vue` edits).
- Comment non-obvious layout logic (grid sizing, drawer behaviour, localStorage guard).

### 8. Verify
Run the dev server and check, at **1280px, 900px and 375px** widths:
- Every route renders; the correct nav item is active (and only one).
- Collapse toggle works and persists across reload; drawer opens/closes on mobile, closes on navigation.
- Existing features still work (filters refetch, modals open, language switch updates labels).
- Keyboard: Tab reaches every nav item with a visible focus ring; Escape closes the drawer.
- No new console errors; no horizontal page scroll at any width. Measure it (`scrollWidth` against `innerWidth`) rather than eyeballing a screenshot.
- At 375px, in drawer mode: open the drawer and confirm it sits flush left at full width, focus moves into it, and Escape returns focus to the hamburger. In rail mode: confirm the rail is icons-only, every icon has a tooltip and an accessible name, and the topbar and content still fit the remaining width.
- Take before/after screenshots for the user.

## Done when
- [ ] Top nav removed; sidebar + topbar shell in place
- [ ] Tokens on `:root`, derived from the existing palette; shared classes use them
- [ ] Sidebar expands, collapses, and works on phones in the chosen mode (drawer or icon rail)
- [ ] All routes, filters, modals and i18n behave as before
- [ ] No new dependencies, no logic changes, no new console errors
- [ ] Verified at desktop / tablet / mobile widths, screenshots shared
