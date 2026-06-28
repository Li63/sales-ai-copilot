from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    msg_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    seq: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    from_user: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    to_user: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    msg_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    msg_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    room_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    contact_name: Mapped[str | None] = mapped_column(String(64))
    contact_phone: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="approved")
    created_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(64))
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="sales")
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"), nullable=True, index=True)
    approval_status: Mapped[str] = mapped_column(String(16), nullable=False, default="approved")
    created_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime)
    industry: Mapped[str | None] = mapped_column(String(128))
    customer_group: Mapped[str | None] = mapped_column(String(255))
    sales_guide: Mapped[str | None] = mapped_column(Text)
    memory_summary: Mapped[str | None] = mapped_column(Text)

    tenant: Mapped[Tenant | None] = relationship()

    @property
    def sales_userid(self) -> str:
        return f"user-{self.id}"


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("follow_userid", "external_userid", name="uk_follow_external"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    external_userid: Mapped[str] = mapped_column(String(64), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(128))
    avatar: Mapped[str | None] = mapped_column(String(255))
    gender: Mapped[int] = mapped_column(default=0)
    region: Mapped[str | None] = mapped_column(String(128))
    remark: Mapped[str | None] = mapped_column(String(255))
    add_time: Mapped[datetime | None] = mapped_column(DateTime)
    add_channel: Mapped[str | None] = mapped_column(String(64))
    follow_userid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    intention_level: Mapped[str] = mapped_column(String(16), default="C")
    intention_score: Mapped[int] = mapped_column(default=50)
    last_chat_time: Mapped[datetime | None] = mapped_column(DateTime)
    core_demand: Mapped[str | None] = mapped_column(String(128))
    objection: Mapped[str | None] = mapped_column(String(128))
    persona_profile: Mapped[str | None] = mapped_column(Text)
    persona_updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    lifecycle_status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)

    tags: Mapped[list["CustomerTag"]] = relationship(back_populates="customer", cascade="all, delete-orphan")


class CustomerTag(Base):
    __tablename__ = "customer_tags"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    tag_name: Mapped[str] = mapped_column(String(64), nullable=False)
    tag_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=1.0)

    customer: Mapped[Customer] = relationship(back_populates="tags")


class FollowRecord(Base):
    __tablename__ = "follow_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    sales_userid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    next_follow_time: Mapped[datetime | None] = mapped_column(DateTime)


class ReplyFeedback(Base):
    __tablename__ = "reply_feedbacks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    sales_userid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    external_userid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    original_customer_question: Mapped[str | None] = mapped_column(Text)
    ai_reply: Mapped[str] = mapped_column(Text, nullable=False)
    customer_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False, default="neutral")
    lesson: Mapped[str | None] = mapped_column(Text)


class GlobalSalesInsight(Base):
    __tablename__ = "global_sales_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    insight_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_window_start: Mapped[datetime | None] = mapped_column(DateTime)
    source_window_end: Mapped[datetime | None] = mapped_column(DateTime)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sample_count: Mapped[int] = mapped_column(default=0)


class PersonaSource(Base):
    __tablename__ = "persona_sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    sales_userid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    external_userid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    title: Mapped[str | None] = mapped_column(String(128))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    persona_summary: Mapped[str | None] = mapped_column(Text)


class IpContentRecord(Base):
    __tablename__ = "ip_content_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sales_userid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    theme: Mapped[str] = mapped_column(String(128), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="moments")
    content: Mapped[str] = mapped_column(Text, nullable=False)


class CompanyMaterial(Base):
    __tablename__ = "company_materials"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sales_userid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"), nullable=True, index=True)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    scope: Mapped[str] = mapped_column(String(16), nullable=False, default="sales")
    approval_status: Mapped[str] = mapped_column(String(16), nullable=False, default="approved")
    effective: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    content: Mapped[str] = mapped_column(Text, nullable=False)


class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sales_userid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    external_userid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    request_payload: Mapped[str] = mapped_column(Text, nullable=False)
    response_payload: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)


class SyncState(Base):
    __tablename__ = "sync_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sync_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    sync_value: Mapped[str] = mapped_column(String(255), nullable=False)
