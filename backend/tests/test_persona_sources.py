from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.core.database import Base, get_db
from app.main import app
from app.models import Customer, PersonaSource, Tenant, User
from app.services.llm_service import LLMService


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
