import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.core.database import Base, get_db
from app.main import app
from app.models import Customer, PersonaSource, Tenant, User
from app.services.llm_service import LLMService


@pytest.fixture(autouse=True)
def disable_douyin_link_resolution(monkeypatch):
    async def no_resolution(url: str):
        return None

    monkeypatch.setattr("app.api.routes._resolve_douyin_link", no_resolution, raising=False)


def _client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session_local = sessionmaker(bind=engine)

    db = testing_session_local()
    db.add_all(
        [
            Tenant(id=1, name="测试企业", status="approved"),
            User(
                id=1,
                username="sales",
                password_hash="x",
                display_name="销售",
                role="sales",
                tenant_id=1,
                approval_status="approved",
            ),
            Customer(
                id=1,
                external_userid="external-1",
                follow_userid="user-1",
                nickname="客户A",
                intention_level="C",
                intention_score=50,
            ),
        ]
    )
    db.commit()
    db.close()

    class FakeLLM(LLMService):
        async def analyze_persona_source(
            self,
            content,
            customer_profile=None,
            source_type="manual",
            source_url="",
        ):
            return f"来源类型：{source_type}\n原始链接：{source_url}\n核心判断：{content[:20]}"

        async def analyze_persona_images(
            self,
            images,
            customer_profile=None,
            source_type="manual",
            source_url="",
            text_context="",
        ):
            return (
                f"截图类型：抖音作品截图\n"
                f"来源类型：{source_type}\n"
                f"原始链接：{source_url}\n"
                f"企业定位：客户是食品机械设备厂家。\n"
                f"实力证据：截图数量 {len(images)}，{text_context[:30]}"
            )

    def override_db():
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[deps.get_llm_service] = lambda: FakeLLM(api_key="", base_url="", model="")
    return TestClient(app), testing_session_local


def test_persona_source_add_accepts_douyin_source_url():
    client, session_local = _client()
    try:
        response = client.post(
            "/api/persona/source/add",
            json={
                "sales_userid": "user-1",
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

        db = session_local()
        source = db.query(PersonaSource).one()
        assert source.source_url == "https://www.douyin.com/user/example"
        db.close()
    finally:
        app.dependency_overrides.clear()


def test_persona_source_add_infers_douyin_content_from_share_text():
    client, session_local = _client()
    try:
        share_text = (
            "2.56 复制打开抖音，看看【金林食品机械设备厂家的作品】"
            "瓜果蔬菜萝卜切条机 # 萝卜切条机# 果蔬推条机#... "
            "https://v.douyin.com/VhrrmUHw3SM/ 10/01 kPx:/ m@Q.XM :9pm"
        )
        response = client.post(
            "/api/persona/source/add",
            json={
                "sales_userid": "user-1",
                "external_userid": "external-1",
                "source_type": "manual",
                "title": "抖音分享",
                "content": share_text,
            },
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["source_type"] == "douyin_content"
        assert payload["source_url"] == "https://v.douyin.com/VhrrmUHw3SM/"

        db = session_local()
        source = db.query(PersonaSource).one()
        assert "平台：抖音" in source.content
        assert "账号：金林食品机械设备厂家" in source.content
        assert "作品线索：瓜果蔬菜萝卜切条机" in source.content
        assert "标签：萝卜切条机、果蔬推条机" in source.content
        db.close()
    finally:
        app.dependency_overrides.clear()


def test_persona_source_add_accepts_url_only_as_pending_evidence():
    client, session_local = _client()
    try:
        response = client.post(
            "/api/persona/source/add",
            json={
                "sales_userid": "user-1",
                "external_userid": "external-1",
                "source_type": "manual",
                "source_url": "https://v.douyin.com/VhrrmUHw3SM/",
                "title": "抖音短链",
                "content": "",
            },
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["source_type"] == "douyin_content"
        assert payload["source_url"] == "https://v.douyin.com/VhrrmUHw3SM/"

        db = session_local()
        source = db.query(PersonaSource).one()
        assert "用户只提供了链接" in source.content
        assert "不能当成已抓取完整页面" in source.content
        db.close()
    finally:
        app.dependency_overrides.clear()


def test_persona_source_add_enriches_douyin_link_when_public_resolver_succeeds(monkeypatch):
    async def fake_resolve_douyin_link(url: str):
        assert url == "https://v.douyin.com/VhrrmUHw3SM/"
        return {
            "status": "resolved",
            "source_url": url,
            "final_url": "https://www.douyin.com/video/7656390840890654457",
            "video_id": "7656390840890654457",
            "title": "金林食品机械设备厂家的作品：瓜果蔬菜萝卜切条机",
            "description": "瓜果蔬菜萝卜切条机 #萝卜切条机 #果蔬推条机",
            "cover_url": "https://example.test/cover.jpg",
            "redirect_chain": [url, "https://www.douyin.com/video/7656390840890654457"],
            "missing_fields": ["评论"],
        }

    monkeypatch.setattr("app.api.routes._resolve_douyin_link", fake_resolve_douyin_link)
    client, session_local = _client()
    try:
        response = client.post(
            "/api/persona/source/add",
            json={
                "sales_userid": "user-1",
                "external_userid": "external-1",
                "source_type": "manual",
                "source_url": "https://v.douyin.com/VhrrmUHw3SM/",
                "title": "抖音链接",
                "content": "",
            },
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["source_url"] == "https://www.douyin.com/video/7656390840890654457"

        db = session_local()
        source = db.query(PersonaSource).one()
        assert "解析方式：抖音公开链接解析" in source.content
        assert "视频ID：7656390840890654457" in source.content
        assert "作品标题：金林食品机械设备厂家的作品：瓜果蔬菜萝卜切条机" in source.content
        assert "未获取字段：评论" in source.content
        db.close()
    finally:
        app.dependency_overrides.clear()


def test_persona_intelligence_analyze_uses_multimodal_images_directly():
    client, session_local = _client()
    try:
        response = client.post(
            "/api/persona/intelligence/analyze",
            data={
                "sales_userid": "user-1",
                "external_userid": "external-1",
                "source_type": "douyin_content",
                "source_url": "https://v.douyin.com/VhrrmUHw3SM/",
                "title": "抖音作品截图",
                "content": "销售补充：客户发的是萝卜切条机作品截图。",
            },
            files={"files": ("douyin.png", b"fake-image", "image/png")},
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["source_type"] == "douyin_content"
        assert "截图类型：抖音作品截图" in payload["persona_summary"]
        assert "企业定位：客户是食品机械设备厂家。" in payload["persona_summary"]

        db = session_local()
        source = db.query(PersonaSource).one()
        assert "多模态截图分析" in source.content
        assert "销售补充：客户发的是萝卜切条机作品截图。" in source.content
        db.close()
    finally:
        app.dependency_overrides.clear()


def test_persona_source_add_normalizes_unknown_source_type():
    client, _ = _client()
    try:
        response = client.post(
            "/api/persona/source/add",
            json={
                "sales_userid": "user-1",
                "external_userid": "external-1",
                "source_type": "unknown-platform",
                "title": "未知资料",
                "content": "销售线下观察到客户关注交付稳定。",
            },
        )

        assert response.status_code == 200
        assert response.json()["data"]["source_type"] == "manual"
    finally:
        app.dependency_overrides.clear()


def test_refresh_customer_persona_keeps_source_type_and_hypothesis_warning():
    client, session_local = _client()
    try:
        response = client.post(
            "/api/persona/source/add",
            json={
                "sales_userid": "user-1",
                "external_userid": "external-1",
                "source_type": "qichacha",
                "source_url": "https://www.qcc.com/firm/example",
                "title": "企查查资料",
                "content": "经营范围包含企业服务，近期有招聘信息。",
            },
        )

        assert response.status_code == 200
        db = session_local()
        customer = db.query(Customer).filter_by(external_userid="external-1").one()
        assert "销售假设" in customer.persona_profile
        assert "企查查资料" in customer.persona_profile
        db.close()
    finally:
        app.dependency_overrides.clear()
