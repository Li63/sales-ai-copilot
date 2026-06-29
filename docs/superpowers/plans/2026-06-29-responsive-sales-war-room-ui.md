# Responsive Sales War Room UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a responsive, premium "销冠作战指挥舱" UI for desktop, tablet, and phone.

**Architecture:** Keep the current Vue 3 + Vant component model. Add a stronger CSS token layer, then upgrade the app shell and high-traffic pages with responsive grids and adaptive navigation. Avoid introducing Tailwind/shadcn because this project is Vue/Vant and already uses scoped CSS.

**Tech Stack:** Vue 3, Vant 4, TypeScript, custom CSS, CSS variables, Vite.

## Global Constraints

- Keep Vue 3 + Vant; do not add a heavy UI framework.
- Keep existing component props, emits, and store actions.
- Phone `< 760px`, tablet `760px - 1179px`, desktop `>= 1180px`.
- Desktop must not look like a stretched mobile sidebar.
- Server deployment may only touch `/data/sales-ai/app`.

---

### Task 1: Global Design Tokens

**Files:**
- Modify: `frontend/src/styles/base.css`

**Interfaces:**
- Produces CSS variables used by existing scoped component CSS: `--bg`, `--surface`, `--ink`, `--brand`, `--radius-*`, `--shadow-*`.

- [ ] Replace the current soft mobile palette with premium command-center tokens.
- [ ] Add global body background layers and selection/focus treatment.
- [ ] Add reusable page width variables: `--shell-max`, `--rail-width`, `--page-gap`.
- [ ] Verify existing components still compile with the same variables.

### Task 2: App Shell And Navigation

**Files:**
- Modify: `frontend/src/App.vue`

**Interfaces:**
- Consumes: existing `active` tab index and `navItems`.
- Produces: responsive shell where desktop uses a left visual rail and mobile uses bottom nav.

- [ ] Add semantic classes to the workspace wrapper while keeping current Vue conditional rendering.
- [ ] Redesign `.shell`, `.workspace-bar`, `.content`, `.bottom-nav`.
- [ ] At `>= 1180px`, turn `.bottom-nav` into a left rail and reserve content margin.
- [ ] At `< 760px`, keep bottom nav with safe area and compact header.

### Task 3: Core Page Responsiveness

**Files:**
- Modify: `frontend/src/components/CustomerHeader.vue`
- Modify: `frontend/src/components/RecommendationTab.vue`
- Modify: `frontend/src/components/ProfileTab.vue`

**Interfaces:**
- Consume existing props/emits only.
- Produce adaptive card grids and premium surfaces for customer header,作战页, and画像页.

- [ ] Upgrade `CustomerHeader` to desktop-grade identity strip with responsive meta cells.
- [ ] Upgrade `RecommendationTab` so desktop uses a 12-column dashboard grid and mobile remains single-column.
- [ ] Upgrade `ProfileTab` so battle cards/source workflow use 4/2/1-column responsive grids.
- [ ] Keep all inputs/buttons accessible and visible on phone.

### Task 4: Verification And Deployment

**Files:**
- Modify as needed from Tasks 1-3.

**Interfaces:**
- Produces pushed PR branch and deployed app under `/data/sales-ai/app`.

- [ ] Run `cd frontend && npm run build`.
- [ ] Run backend tests if backend files changed.
- [ ] Push branch `codex/douyin-qichacha-persona`.
- [ ] Deploy only to `/data/sales-ai/app`, preserving `.env`, certs, outputs, work, `.agents`, `.codex`.
- [ ] Verify backend health, nginx health, frontend 200, and unchanged MySQL/Redis container IDs.
