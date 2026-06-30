# Sales War Room UI Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the frontend visual system into a clean sales command center while preserving current product behavior.

**Architecture:** This is a CSS and template-light refresh on the existing Vue + Vant app. Global tokens define the new visual language, while core screens adopt shared card, button, input, and navigation treatments.

**Tech Stack:** Vue 3, Vite, Vant, scoped CSS, existing Pinia store.

## Global Constraints

- Keep Vue + Vant architecture.
- Do not add a new component framework.
- Keep existing business behavior and API calls unchanged.
- Preserve mobile usability first.
- Verify with `npm run build`.

---

### Task 1: Global Visual Tokens

**Files:**
- Modify: `frontend/src/styles/base.css`

**Steps:**
- [ ] Replace current flat teal tokens with clean war-room tokens: ink navy, teal, amber, ivory surfaces.
- [ ] Add body background atmosphere with subtle radial/linear gradients.
- [ ] Improve base input, textarea, button focus, Vant tab, and reduced-motion styles.
- [ ] Run `npm run build` after component updates.

### Task 2: App Shell And Navigation

**Files:**
- Modify: `frontend/src/App.vue`

**Steps:**
- [ ] Restyle `.shell` as a centered glass-like app surface.
- [ ] Restyle `.workspace-bar` as a premium command header.
- [ ] Restyle `.bottom-nav` into a clean floating command dock.
- [ ] Keep existing navigation items and click behavior unchanged.

### Task 3: Core Sales Screens

**Files:**
- Modify: `frontend/src/components/CustomerHeader.vue`
- Modify: `frontend/src/components/RecommendationTab.vue`
- Modify: `frontend/src/components/ProfileTab.vue`
- Modify: `frontend/src/components/SummaryDashboard.vue`
- Modify: `frontend/src/components/CustomerLibrary.vue`

**Steps:**
- [ ] Apply consistent cards, rounded corners, spacing, and shadows.
- [ ] Differentiate action cards from insight cards through color and borders.
- [ ] Preserve all props, emits, form bindings, and store calls.
- [ ] Keep responsive behavior readable on narrow mobile screens.

### Task 4: Verification

**Files:**
- Test: `frontend`

**Steps:**
- [ ] Run `npm run build` in `frontend`.
- [ ] Check local preview loads.
- [ ] Review changed files with `git diff`.
