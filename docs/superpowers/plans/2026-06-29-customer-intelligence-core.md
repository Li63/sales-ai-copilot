# Customer Intelligence Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the persona tab into a customer intelligence core that auto-analyzes uploads, parses Douyin share text, hides long source records, and outputs enterprise-level battle cards.

**Architecture:** Backend enriches incoming persona sources into structured evidence before LLM analysis. Frontend provides one intelligence intake workflow and auto-submits extracted files after OCR. Existing APIs remain compatible.

**Tech Stack:** FastAPI, SQLAlchemy, pytest, Vue 3, Pinia, Vant, TypeScript.

## Global Constraints

- Keep Vue 3 + Vant; do not add a heavy UI framework.
- Keep `/api/persona/source/add` backward compatible.
- Only parse Douyin share text/link unless reliable page fetch exists; never pretend fetched video details.
- Hide long source records by default.
- Server deployment may only touch `/data/sales-ai/app`.

---

### Task 1: Backend Evidence Enrichment

**Files:**
- Modify: `backend/app/api/routes.py`
- Modify: `backend/tests/test_persona_sources.py`

**Interfaces:**
- Consumes: `PersonaSourceRequest(title, content, source_type, source_url)`
- Produces: `_prepare_persona_source_input(title, content, source_type, source_url) -> tuple[str, str, str, str]`

- [ ] Add tests that Douyin share text is accepted, inferred as `douyin_content`, and stored as structured evidence.
- [ ] Add tests that URL-only source can be analyzed instead of rejected.
- [ ] Implement helpers for URL extraction, source type inference, and Douyin share evidence formatting.
- [ ] Run `pytest tests/test_persona_sources.py -q`.

### Task 2: Frontend Auto-Analysis Workflow

**Files:**
- Modify: `frontend/src/components/ProfileTab.vue`

**Interfaces:**
- Consumes: existing `addPersona` emit.
- Produces: auto-submit after file extraction and manual one-click intelligence submission.

- [ ] Replace manual source selection emphasis with one intake card.
- [ ] Auto-detect source type from pasted content/link.
- [ ] Upload files, append extracted text, and immediately emit `addPersona`.
- [ ] Hide source records behind a collapsible details panel.
- [ ] Run `cd frontend && npm run build`.

### Task 3: LLM Output Strengthening

**Files:**
- Modify: `backend/app/services/llm_service.py`
- Modify: `backend/tests/test_llm_service.py`

**Interfaces:**
- Consumes: enriched persona source content.
- Produces: formatted sections for enterprise analysis and sales battle cards.

- [ ] Add expectations for enterprise positioning, strength, purchase motivation, and icebreaker fields.
- [ ] Update prompt and fallback formatter.
- [ ] Run `pytest tests/test_llm_service.py tests/test_persona_sources.py -q`.

### Task 4: Verify, Push, Deploy

**Files:**
- Modify as needed from tasks above.

**Interfaces:**
- Consumes: working code from Tasks 1-3.
- Produces: updated PR branch and deployed `/data/sales-ai/app`.

- [ ] Run `cd frontend && npm run build`.
- [ ] Run backend persona/LLM tests.
- [ ] Commit and push branch.
- [ ] Deploy only to `/data/sales-ai/app`, preserving `.env`, certs, outputs, work, `.agents`, `.codex`.
- [ ] Verify backend health, nginx health, frontend 200, and that MySQL/Redis were not rebuilt.
