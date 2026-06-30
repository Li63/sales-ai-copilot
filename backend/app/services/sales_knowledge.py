from datetime import datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import ChatMessage, Customer, GlobalSalesInsight, ReplyFeedback, SyncState


REFRESH_KEY = "global_sales_insights_last_refresh"
REFRESH_DAYS = 5


DEFAULT_SALES_PLAYBOOK = """# 共享销售技巧库

## 基础对话原则
- 先接住情绪，再问清事实，再给判断标准，最后推进一个低压小动作。
- 不要一上来介绍产品，先判断客户阶段：陌生、了解、比较、强意向、待成交、沉睡。
- 新销售没有历史数据时，默认用顾问型销冠打法：少压迫、多确认、用案例和判断标准降低客户风险感。
- 所有话术都要像真人销售，不要像客服模板；短句、具体、给选择权。

## 电话沟通
- 前 15 秒说清身份、来源、占用时间和低压选择。
- 一次只讲一个重点，讲完必须停下来问一句。
- 多问“现在怎么处理、哪里卡、拖下去有什么影响、谁一起判断”，少问“有没有需求”。
- 客户说没时间时，只确认“完全不考虑，还是现在不方便聊”。

## 微信沟通
- 微信不是电话文字版，要短、准、有人味，不连续轰炸。
- 不发“在吗”，用新的价值理由跟进：案例、报价拆分、行业观察、对比清单。
- 回复公式：承接客户原话 + 给判断标准 + 轻推进问题。
- 沉默客户低频触达，不硬催，用朋友圈/IP 内容建立信任。

## 面谈沟通
- 面谈不是讲完 PPT，而是共同确认问题、预算、决策链和下一步。
- 开场先校准议程：先了解情况，再对照能否解决，不合适就直说。
- 结束不说“等您消息”，必须约定资料、方案、复盘或下一次沟通时间。

## 抖音内容销售打法
- 3秒钩子先点出客户卡点：别先讲产品，先讲“客户为什么现在犹豫、为什么问价格、为什么不回复”。
- 先场景后方案：把客户每天遇到的真实场景讲清楚，再给一个判断标准，不要一上来喊口号。
- 证据链比硬承诺更有用：案例、截图、流程、对比、客户原话、交付节点，都比“我们很专业”更可信。
- 评论区是异议库：把评论里的担心整理成销售跟进问题，例如预算、效果、交付、售后、风险。
- 私域承接要轻：客户对内容有兴趣后，用清单、案例、报价拆解或诊断问题承接到微信，不要直接逼成交。
- 不要编造榜单、销量、粉丝量、转化率或“抖音前10销售”这类未验证说法；没有上传或核实的资料，只能当选题灵感。

## 异议处理
- 异议不是反对，通常是客户在确认风险。
- 处理顺序：认同顾虑、澄清原因、拆解问题、给证据、推进小动作。
- 价格异议要拆成：和谁比贵、担心一次性投入、还是担心效果不确定。
"""


class SalesKnowledgeService:
    def __init__(self, db: Session):
        self.db = db

    def build_context(self, limit: int = 8) -> str:
        insights = list(
            self.db.scalars(select(GlobalSalesInsight).order_by(desc(GlobalSalesInsight.created_at)).limit(limit))
        )
        if not insights:
            return DEFAULT_SALES_PLAYBOOK
        blocks = [DEFAULT_SALES_PLAYBOOK, "\n# 近期沉淀的全局销售经验"]
        for item in insights:
            blocks.append(f"\n## {item.title}\n{item.content}")
        return "\n".join(blocks)

    def build_technique_guide(self) -> str:
        return (
            self.build_context()
            .replace("# 共享销售技巧库", "# 销售沟通技巧指南")
            .replace("## 电话沟通", "## 电销沟通技巧指南")
            .replace("## 微信沟通", "## 微信沟通技巧指南")
            .replace("## 面谈沟通", "## 面销沟通技巧指南")
        )

    def refresh_if_due(self, now: datetime | None = None, force: bool = False) -> int:
        now = now or datetime.utcnow()
        state = self.db.scalar(select(SyncState).where(SyncState.sync_key == REFRESH_KEY))
        if state is not None and not force:
            try:
                last_refresh = datetime.fromisoformat(state.sync_value)
                if now - last_refresh < timedelta(days=REFRESH_DAYS):
                    return 0
            except ValueError:
                pass

        window_start = now - timedelta(days=REFRESH_DAYS)
        created = 0
        closed_content, closed_count = self._closed_customer_summary(window_start, now)
        if closed_content:
            self.db.add(
                GlobalSalesInsight(
                    insight_type="closed_success",
                    source_window_start=window_start,
                    source_window_end=now,
                    title="成交客户经验",
                    content=closed_content,
                    sample_count=closed_count,
                )
            )
            created += 1

        d_content, d_count = self._d_customer_summary(window_start, now)
        if d_content:
            self.db.add(
                GlobalSalesInsight(
                    insight_type="d_customer_review",
                    source_window_start=window_start,
                    source_window_end=now,
                    title="D类客户复盘",
                    content=d_content,
                    sample_count=d_count,
                )
            )
            created += 1

        if state is None:
            self.db.add(SyncState(sync_key=REFRESH_KEY, sync_value=now.isoformat()))
        else:
            state.sync_value = now.isoformat()
        self.db.commit()
        return created

    def _closed_customer_summary(self, start: datetime, end: datetime) -> tuple[str, int]:
        _ = start
        customers = list(
            self.db.scalars(
                select(Customer)
                .where(Customer.lifecycle_status == "closed")
                .order_by(desc(Customer.closed_at), desc(Customer.updated_at))
                .limit(20)
            )
        )
        if not customers:
            return "", 0
        lines = [
            "重点参考已成交客户的聊天节奏、客户全景和有效话术：",
            "- 成交客户通常要复用：先确认核心诉求，再处理主要异议，最后明确下一步动作。",
        ]
        for customer in customers[:8]:
            messages = self._recent_messages(customer, limit=4)
            lines.append(
                f"- {customer.nickname or customer.external_userid}：核心诉求={customer.core_demand or '未记录'}；"
                f"主要异议={customer.objection or '未记录'}；人设判断={_clip(customer.persona_profile, 90)}；"
                f"高价值话术/节奏={_clip(' / '.join(messages), 160)}"
            )
        return "\n".join(lines)[:4000], len(customers)

    def _d_customer_summary(self, start: datetime, end: datetime) -> tuple[str, int]:
        _ = (start, end)
        customers = list(
            self.db.scalars(
                select(Customer)
                .where((Customer.intention_score < 20) | (Customer.intention_level == "D"))
                .order_by(desc(Customer.updated_at))
                .limit(20)
            )
        )
        bad_feedback = list(
            self.db.scalars(select(ReplyFeedback).where(ReplyFeedback.outcome == "bad").order_by(desc(ReplyFeedback.created_at)).limit(12))
        )
        if not customers and not bad_feedback:
            return "", 0
        lines = [
            "D类客户和差反馈用于提醒系统少走弯路：",
            "- 遇到低意向客户，先判断是否值得继续投入，不要强推成交。",
            "- 如果客户只剩价格异议或长期沉默，要换成低频价值触达，少连续追问。",
        ]
        for customer in customers[:8]:
            messages = self._recent_messages(customer, limit=3)
            lines.append(
                f"- {customer.nickname or customer.external_userid}：不好点={customer.objection or '未记录'}；"
                f"当前诉求={customer.core_demand or '未记录'}；可复用/需避免话术={_clip(' / '.join(messages), 150)}"
            )
        for item in bad_feedback[:6]:
            lines.append(f"- 差反馈：{_clip(item.lesson or item.customer_feedback, 180)}")
        return "\n".join(lines)[:4000], len(customers) + len(bad_feedback)

    def _recent_messages(self, customer: Customer, limit: int) -> list[str]:
        rows = list(
            self.db.scalars(
                select(ChatMessage)
                .where(
                    ((ChatMessage.from_user == customer.follow_userid) & (ChatMessage.to_user == customer.external_userid))
                    | ((ChatMessage.from_user == customer.external_userid) & (ChatMessage.to_user == customer.follow_userid))
                )
                .order_by(desc(ChatMessage.msg_time))
                .limit(limit)
            )
        )
        return [row.content or "" for row in rows if row.content]


def _clip(value: str | None, limit: int) -> str:
    text = (value or "").strip().replace("\n", " ")
    return text[:limit] if text else "未记录"
