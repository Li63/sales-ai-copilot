# Responsive Sales War Room UI Design

## Goal

Turn the current sidebar-like interface into a responsive "销冠作战指挥舱" that feels high-end, fresh, and usable on desktop, tablet, and phone.

## Product Direction

The system is a daily sales command center, not a generic form app. The UI should make a salesperson feel they are entering a focused operating room for customer judgment, AI strategy, follow-up, and content growth.

## Visual Direction

- Theme: clean premium command center.
- Mood: bright, calm, confident, slightly futuristic.
- Avoid: heavy dark mode, purple SaaS defaults, visual noise, tiny dense mobile-only layout.
- Palette: mineral teal, deep ink blue, warm amber highlights, soft porcelain surfaces.
- Surfaces: layered cards, translucent navigation, subtle radial glows, crisp borders.
- Motion: restrained load/hover transitions, no distracting looping animation except processing states.

## Responsive Breakpoints

- Phone: `< 760px`
  - Single-column card flow.
  - Bottom navigation remains.
  - Header compresses, cards use full width, dense grids collapse.
- Tablet: `760px - 1179px`
  - Centered max-width workspace.
  - Two-column grids where content supports it.
  - Navigation remains bottom or compact top depending available width.
- Desktop: `>= 1180px`
  - Full-width command deck with left rail navigation.
  - Sticky top workspace bar.
  - Main content gets wider card grids and higher information density.
  - Bottom navigation becomes left rail behavior visually, but keeps same Vue state and no route rewrite.

## Scope

- Rework global CSS tokens in `frontend/src/styles/base.css`.
- Rework application shell and navigation in `frontend/src/App.vue`.
- Upgrade `CustomerHeader.vue`, `RecommendationTab.vue`, and `ProfileTab.vue` responsive styling.
- Do not change backend behavior.
- Do not add a new UI framework; keep Vue 3 + Vant + custom CSS.
- Keep existing component APIs and store behavior.

## Acceptance Criteria

- Desktop at 1440px no longer looks like a stretched mobile app.
- Tablet around 900px uses two-column card layout without horizontal scrolling.
- Phone around 390px remains readable with bottom nav and safe-area spacing.
- Core customer intelligence workflow stays visible and usable.
- Build succeeds with `npm run build`.
- Deployment only touches `/data/sales-ai/app` and does not recreate MySQL or Redis.
