# Sales War Room UI Refresh Design

## Goal

Upgrade the product from a plain stacked-form interface into a clean "sales war room" experience: sharper hierarchy, calmer colors, more premium spacing, and clearer action cards.

## Visual Direction

- Theme: clean sales command center, not dark-heavy dashboard.
- Palette: ink navy, fresh teal, warm amber highlights, ivory/white surfaces.
- Layout feel: airy cards, soft glass, subtle gradients, rounded controls, stronger primary actions.
- Tone: confident and practical, suitable for sales teams using it daily.

## Scope

- Refresh global design tokens in `frontend/src/styles/base.css`.
- Refresh the app shell, top workspace bar, busy overlay, and bottom navigation in `frontend/src/App.vue`.
- Refresh the customer context header in `frontend/src/components/CustomerHeader.vue`.
- Refresh the core sales workflow screen in `frontend/src/components/RecommendationTab.vue`.
- Refresh the customer panorama/persona screen in `frontend/src/components/ProfileTab.vue`.
- Refresh overview and customer-library cards where they share the same visual language.

## Constraints

- Keep Vue + Vant architecture.
- Do not add a new component framework.
- Keep existing business behavior and API calls unchanged.
- Preserve mobile usability first, with desktop width still capped at the existing app shell.
- Verify with `npm run build`.
