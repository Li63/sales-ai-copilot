# Douyin Qichacha Persona Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let sales users enrich customer personas with manually provided Douyin, Qichacha, website, and research materials, then use those signals in customer analysis and sales playbooks.

**Architecture:** Extend the existing `PersonaSource` workflow instead of adding a new subsystem. Backend stores `source_url`, normalizes source type, upgrades LLM persona summaries, and feeds richer context into existing analysis calls. Frontend adds source type and URL controls to the current customer panorama panel.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, Vue 3, Pinia, TypeScript, Vite.

## Global Constraints

- Do not build automatic Douyin or Qichacha crawlers.
- Sales users manually paste links, notes, screenshots, PDFs, or Word files.
- Treat uploaded public material as sales hypotheses, not verified facts.
- Preserve the compact enterprise WeChat sidebar information architecture.
- Keep existing authentication behavior unchanged.
- Use UTF-8 for Chinese prompts and guide text.

---

### Task 1: Backend Persona Source Type And URL

**Files:**
- Modify: `backend/app/models/entities.py`
- Modify: `backend/app/api/routes.py`
- Test: `backend/tests/test_persona_sources.py`

**Interfaces:**
- Consumes: existing `/api/persona/source/add` and `/api/persona/source/list`
- Produces: `PersonaSource.source_url: str | None`
- Produces: `_normalize_persona_source_type(source_type: str) -> str`
- Produces: `_persona_source_payload(item: PersonaSource) -> dict` containing `source_url`

- [ ] **Step 1: Write failing backend tests**

```python
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import deps
from app.core.database import Base, get_db
from app.main import app
from app.models import Customer, PersonaSource, Tenant, User
from app.services.llm_service import LLMService


def _client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    db = TestingSessionLocal()
    tenant = Tenant(id=1, name="测试企业", status="approved")
    user = User(
        id=1,
        username="sales",
        password_hash="x",
        display_name="销售",
        role="sales",
        tenant_id=1,
        approval_status="approved",
    )
    customer = Customer(
        id=1,
        external_userid="external-1",
        follow_userid="user-1",
        nickname="客户A",
        intention_level="C",
        intention_score=50,
    )
    db.add_all([tenant, user, customer])
    db.commit()
    db.close()

    class FakeLLM(LLMService):
        async def analyze_persona_source(self, content, customer_profile=None, source_type="manual", source_url=""):
            return f"来源类型：{source_type}\n原始链接：{source_url}\n核心判断：{content[:20]}"

    def override_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.get_llm_service] = lambda: FakeLLM(api_key="", base_url="", model="")
    return TestClient(app), TestingSessionLocal


def test_persona_source_add_accepts_douyin_source_url():
    client, SessionLocal = _client()

    response = client.post(
        "/api/persona/source/add",
        json={
            "sales_userid": "ignored",
            "external_userid": "external-1",
            "source_type": "douyin_profile",
            "source_url": "https://www.douyin.com/user/example",
            "title": "抖音主页",
            "content": "主页简介强调老板IP，作品多在讲成交案例。",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["source_type"] == "douyin_profile"
    assert payload["source_url"] == "https://www.douyin.com/user/example"
    assert "来源类型：douyin_profile" in payload["persona_summary"]

    db = SessionLocal()
    source = db.query(PersonaSource).one()
    assert source.source_url == "https://www.douyin.com/user/example"
    db.close()
    app.dependency_overrides.clear()


def test_persona_source_add_normalizes_unknown_source_type():
    client, _ = _client()

    response = client.post(
        "/api/persona/source/add",
        json={
            "sales_userid": "ignored",
            "external_userid": "external-1",
            "source_type": "unknown-platform",
            "title": "未知资料",
            "content": "销售线下观察到客户关注交付稳定。",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["source_type"] == "manual"
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend; pytest tests/test_persona_sources.py -q`

Expected: FAIL because `source_url` is not stored or returned, and `LLMService.analyze_persona_source` does not accept source metadata.

- [ ] **Step 3: Implement minimal backend support**

Add `source_url` to `PersonaSource`, extend `PersonaSourceRequest`, add `_normalize_persona_source_type()`, pass source type and URL into `analyze_persona_source()`, and include `source_url` in payloads.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend; pytest tests/test_persona_sources.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add backend/app/models/entities.py backend/app/api/routes.py backend/tests/test_persona_sources.py
git commit -m "feat: support persona source metadata"
```

### Task 2: Persona Prompt, Merge, And Sales Playbook

**Files:**
- Modify: `backend/app/services/llm_service.py`
- Modify: `backend/app/services/sales_knowledge.py`
- Modify: `backend/app/api/routes.py`
- Test: `backend/tests/test_llm_service.py`
- Test: `backend/tests/test_sales_knowledge.py`
- Test: `backend/tests/test_persona_sources.py`

**Interfaces:**
- Consumes: `LLMService.analyze_persona_source(content, customer_profile, source_type, source_url)`
- Produces: persona summaries with business clues, positioning, decision logic, follow angle, risk warning, and sales tip
- Produces: `SalesKnowledgeService.build_context()` containing `## 抖音内容销售打法`

- [ ] **Step 1: Write failing tests**

Add assertions:

```python
@pytest.mark.asyncio
async def test_llm_persona_payload_includes_source_type_and_url():
    captured = {}

    async def ok_client(payload):
        captured.update(payload)
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"summary":"客户在抖音强调交付案例。","business_clues":"正在用内容获客。","content_positioning":"老板IP加案例拆解。","communication_style":"喜欢直接看案例。","decision_logic":"先看可信证据，再谈合作。","follow_angle":"用同类案例开场。","risk_warning":"不要夸大粉丝和转化。","sales_tip":"先问最近内容获客卡点。"}'
                    }
                }
            ]
        }

    service = LLMService(api_key="x", base_url="https://example.test", model="deepseek-chat", http_client=ok_client)
    result = await service.analyze_persona_source(
        "抖音主页内容多为案例拆解。",
        customer_profile={"nickname": "王总"},
        source_type="douyin_profile",
        source_url="https://www.douyin.com/user/example",
    )

    user_payload = captured["messages"][1]["content"]
    assert "douyin_profile" in user_payload
    assert "https://www.douyin.com/user/example" in user_payload
    assert "经营线索" in result
    assert "内容定位" in result
    assert "决策逻辑" in result
```

```python
def test_default_sales_playbook_includes_douyin_content_sales_method():
    playbook = SalesKnowledgeService(_db()).build_context()

    assert "抖音内容销售打法" in playbook
    assert "3秒钩子" in playbook
    assert "私域承接" in playbook
    assert "不要编造榜单" in playbook
```

```python
def test_refresh_customer_persona_keeps_source_type_and_hypothesis_warning():
    client, SessionLocal = _client()

    response = client.post(
        "/api/persona/source/add",
        json={
            "sales_userid": "ignored",
            "external_userid": "external-1",
            "source_type": "qichacha",
            "source_url": "https://www.qcc.com/firm/example",
            "title": "企查查资料",
            "content": "经营范围包含企业服务，近期有招聘信息。",
        },
    )

    assert response.status_code == 200
    db = SessionLocal()
    customer = db.query(Customer).filter_by(external_userid="external-1").one()
    assert "销售假设" in customer.persona_profile
    assert "企查查资料" in customer.persona_profile
    db.close()
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend; pytest tests/test_llm_service.py::test_llm_persona_payload_includes_source_type_and_url tests/test_sales_knowledge.py::test_default_sales_playbook_includes_douyin_content_sales_method tests/test_persona_sources.py::test_refresh_customer_persona_keeps_source_type_and_hypothesis_warning -q`

Expected: FAIL because prompt fields, playbook section, and merge warning are not implemented.

- [ ] **Step 3: Implement prompt, formatter, fallback, merge, and playbook**

Update `PERSONA_ANALYSIS_PROMPT`, `analyze_persona_source()`, `_format_persona_analysis()`, `fallback_persona_analysis()`, `_refresh_customer_persona()`, and `DEFAULT_SALES_PLAYBOOK`.

- [ ] **Step 4: Run focused tests**

Run: `cd backend; pytest tests/test_llm_service.py tests/test_sales_knowledge.py tests/test_persona_sources.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add backend/app/services/llm_service.py backend/app/services/sales_knowledge.py backend/app/api/routes.py backend/tests/test_llm_service.py backend/tests/test_sales_knowledge.py backend/tests/test_persona_sources.py
git commit -m "feat: enrich persona analysis from research sources"
```

### Task 3: Frontend Persona Source Form

**Files:**
- Modify: `frontend/src/stores/sidebar.ts`
- Modify: `frontend/src/components/ProfileTab.vue`

**Interfaces:**
- Consumes: `/api/persona/source/add`
- Produces: `addPersonaSource(payload: { title: string; content: string; source_type: string; source_url?: string })`

- [ ] **Step 1: Update TypeScript types and component form**

Add `source_url` to `PersonaSource`, add it to `addPersonaSource()`, and add source type plus URL controls in `ProfileTab.vue`.

- [ ] **Step 2: Run frontend build**

Run: `cd frontend; npm run build`

Expected: PASS.

- [ ] **Step 3: Commit**

Run:

```bash
git add frontend/src/stores/sidebar.ts frontend/src/components/ProfileTab.vue
git commit -m "feat: add persona research source form"
```

### Task 4: Final Verification

**Files:**
- Verify full backend and frontend.

- [ ] **Step 1: Run backend tests**

Run: `cd backend; pytest -q`

Expected: PASS.

- [ ] **Step 2: Run frontend build**

Run: `cd frontend; npm run build`

Expected: PASS.

- [ ] **Step 3: Inspect git status**

Run: `git status --short --branch`

Expected: clean working tree on `main`.
