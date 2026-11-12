# Worked example: Factory Inventory Management System

How the skill's workflow maps onto this repo (`client/`).

## Discover
- **Routes** (`client/src/main.js`): `/` Dashboard, `/inventory`, `/orders`, `/spending` (labelled "Finance"), `/demand` ("Demand Forecast"), `/reports`. `views/Backlog.vue` exists but is not routed; leave it alone.
- **Current shell** (`client/src/App.vue`): `header.top-nav` holds the logo (`t('nav.companyName')` + `t('nav.subtitle')`), six `router-link` tabs, `<LanguageSwitcher />` and `<ProfileMenu>`. `ProfileMenu` emits `show-profile-details` and `show-tasks`, which open `ProfileDetailsModal` and `TasksModal` in `App.vue`.
- **Bar under the nav:** `<FilterBar />` (Time Period, Location, Category, Order Status), backed by the shared `useFilters` composable. Keep it as a sticky bar at the top of the content area.
- **Styles:** global, unscoped `<style>` in `App.vue`. Shared classes: `.page-header`, `.stats-grid`, `.stat-card`, `.card`, `.card-header`, `.card-title`, `.table-container`, `.badge.*`, `.loading`, `.error`.
- **Palette** (from CLAUDE.md): slate `#0f172a`, `#64748b`, `#e2e8f0`; status green / blue / yellow / red.
- **i18n:** `useI18n().t('nav.*')`, with locales in `client/src/locales/en.js` and `ja.js`. The "Reports" tab is hard-coded, so add `nav.reports` to both locales.
- **Project rules:** no emojis in the UI, and any `.vue` create or modify goes through the `vue-expert` subagent.

## What changes
| File | Change |
|---|---|
| `client/src/App.vue` | Grid shell, tokens on `:root`, shared classes restyled with tokens; keeps modals + task handlers |
| `client/src/components/layout/AppSidebar.vue` | New (from reference) |
| `client/src/components/layout/AppTopbar.vue` | New: page title, hamburger, `LanguageSwitcher`, `ProfileMenu` (events re-emitted to App) |
| `client/src/locales/en.js`, `ja.js` | Add `nav.reports` |
| Views | Only straight token swaps, if any |

## What stays exactly the same
`api.js`, `main.js` routes, `useFilters`, `useAuth`, `useI18n`, every view's script, `FilterBar`, `ProfileMenu`, `LanguageSwitcher` and the modals' contracts.
