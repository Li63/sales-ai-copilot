from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models import ChatMessage, Customer
from app.services.llm_service import LLMService
from app.services.sales_knowledge import SalesKnowledgeService


def _db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_default_sales_playbook_covers_core_channels():
    playbook = SalesKnowledgeService(_db()).build_context()

    assert "电话" in playbook
    assert "微信" in playbook
    assert "面谈" in playbook
    assert "先接住情绪" in playbook


def test_refresh_global_insights_summarizes_closed_and_d_customers():
    db = _db()
    closed = Customer(
        id=1,
        external_userid="closed-customer",
        follow_userid="user-1",
        nickname="成交客户",
        lifecycle_status="closed",
        closed_at=datetime.utcnow(),
        intention_level="S",
        intention_score=92,
        core_demand="确认报价",
        objection="担心售后",
        persona_profile="客户重视安全感，喜欢短句确认。",
    )
    cold = Customer(
        id=2,
        external_userid="cold-customer",
        follow_userid="user-1",
        nickname="D类客户",
        lifecycle_status="active",
        intention_level="C",
        intention_score=15,
        core_demand="只问价格",
        objection="觉得贵",
    )
    db.add_all([closed, cold])
    db.flush()
    db.add_all(
        [
            ChatMessage(
                id=1,
                msg_id="m1",
                seq=0,
                action="send",
                from_user="user-1",
                to_user="closed-customer",
                msg_type="text",
                content="我先帮您拆费用和售后保障。",
                msg_time=datetime.utcnow(),
            ),
            ChatMessage(
                id=2,
                msg_id="m2",
                seq=0,
                action="send",
                from_user="cold-customer",
                to_user="user-1",
                msg_type="text",
                content="太贵了，先不考虑。",
                msg_time=datetime.utcnow(),
            ),
        ]
    )
    db.commit()

    service = SalesKnowledgeService(db)
    created = service.refresh_if_due(now=datetime.utcnow())
    context = service.build_context()

    assert created == 2
    assert "成交客户经验" in context
    assert "D类客户复盘" in context
    assert "确认报价" in context
    assert "觉得贵" in context


def test_refresh_global_insights_skips_when_not_due():
    db = _db()
    service = SalesKnowledgeService(db)

    assert service.refresh_if_due(now=datetime.utcnow()) == 0
    assert service.refresh_if_due(now=datetime.utcnow() + timedelta(days=1)) == 0


def test_force_refresh_can_capture_new_closed_customer_before_five_days():
    db = _db()
    service = SalesKnowledgeService(db)
    now = datetime.utcnow()

    assert service.refresh_if_due(now=now) == 0
    db.add(
        Customer(
            id=1,
            external_userid="closed-now",
            follow_userid="user-1",
            nickname="刚成交客户",
            lifecycle_status="closed",
            closed_at=now,
            intention_level="S",
            intention_score=96,
            core_demand="马上签约",
        )
    )
    db.commit()

    assert service.refresh_if_due(now=now + timedelta(hours=1), force=True) == 1
    assert "马上签约" in service.build_context()


@pytest.mark.asyncio
async def test_llm_payload_includes_shared_sales_playbook():
    captured = {}

    async def ok_client(payload):
        captured.update(payload["messages"][1])
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"core_demand":"看价格","objection":"","reply_suggestions":["a","b","c"],"reply_explanations":["e1","e2","e3"],"next_action":"确认预算","new_tags":[]}'
                    }
                }
            ]
        }

    service = LLMService(api_key="x", base_url="https://example.test", model="deepseek-chat", http_client=ok_client)
    await service.analyze_realtime({}, [], "", sales_playbook="共享销售技巧库")

    assert "共享销售技巧库" in captured["content"]
