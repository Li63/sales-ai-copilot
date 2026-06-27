import hashlib
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer, CustomerTag
from app.services.profile_engine import ProfileEngine


class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.profile_engine = ProfileEngine()

    def get_or_create_customer(self, sales_userid: str, external_userid: str) -> Customer:
        customer = self.db.scalar(
            select(Customer).where(
                Customer.follow_userid == sales_userid,
                Customer.external_userid == external_userid,
            )
        )
        if customer:
            return customer
        customer = Customer(
            follow_userid=sales_userid,
            external_userid=external_userid,
            nickname=external_userid,
            intention_level="C",
            intention_score=50,
        )
        self.db.add(customer)
        self.db.flush()
        return customer

    def create_manual_customer(self, sales_userid: str, nickname: str) -> Customer:
        name = nickname.strip()[:128]
        digest = hashlib.sha256(f"{sales_userid}|{name}".encode("utf-8")).hexdigest()[:24]
        external_userid = f"manual-{digest}"
        customer = self.get_or_create_customer(sales_userid, external_userid)
        customer.nickname = name or customer.nickname
        self.db.flush()
        return customer

    def apply_profile(self, customer: Customer, messages: list[dict]) -> Customer:
        result = self.profile_engine.analyze_messages(messages)
        customer.intention_score = result.intention_score
        customer.intention_level = result.intention_level
        customer.core_demand = result.core_demand
        customer.objection = result.objection
        customer.last_chat_time = datetime.utcnow()

        existing = [
            {"tag_name": tag.tag_name, "tag_type": tag.tag_type, "source": tag.source, "confidence": float(tag.confidence)}
            for tag in customer.tags
        ]
        incoming = [
            {"tag_name": tag.name, "tag_type": tag.type, "source": tag.source, "confidence": tag.confidence}
            for tag in result.tags
        ]
        merged = self.profile_engine.merge_tags(existing, incoming)

        customer.tags.clear()
        for tag in merged:
            customer.tags.append(
                CustomerTag(
                    tag_name=tag["tag_name"],
                    tag_type=tag["tag_type"],
                    source=tag["source"],
                    confidence=tag["confidence"],
                )
            )
        self.db.flush()
        return customer
