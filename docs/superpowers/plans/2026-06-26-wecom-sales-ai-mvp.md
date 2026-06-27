# WeCom Sales AI MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a runnable MVP skeleton for a WeCom sidebar sales AI assistant with real API integration points reserved.

**Architecture:** FastAPI provides business APIs, WeCom adapters, profile scoring, and LLM analysis. Vue 3 renders a compact 360px sidebar and calls the backend. Docker Compose wires backend, frontend static hosting, MySQL, Redis, and Nginx.

**Tech Stack:** Python 3.10+, FastAPI, SQLAlchemy, Pydantic, pytest, Vue 3, Vite, Vant, Pinia, Axios, Docker, Nginx.

## Global Constraints

- Secrets must come from `.env` and never be hard-coded.
- Automatic message sending is not implemented.
- MVP processes only one-to-one text chat records.
- The official WeCom Finance SDK is isolated behind an adapter.
- Sidebar UX is a work surface, not a landing page.

---

## Tasks

- [x] Save design and implementation plan docs.
- [x] Write backend tests for profile, LLM fallback, token cache, and API response format.
- [x] Implement backend app, models, services, and routes.
- [x] Implement frontend Vue sidebar.
- [x] Add environment examples and Docker deployment files.
- [ ] Run backend tests and frontend build checks.
