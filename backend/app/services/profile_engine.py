from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileTag:
    name: str
    type: str
    source: str = "auto"
    confidence: float = 0.8


@dataclass(frozen=True)
class ProfileResult:
    intention_score: int
    intention_level: str
    tags: list[ProfileTag]
    core_demand: str
    objection: str


class ProfileEngine:
    demand_rules = {
        "关注价格": ("demand", ["价格", "报价", "多少钱", "费用", "优惠", "预算"]),
        "关注功能": ("demand", ["功能", "支持", "能不能", "可以实现", "怎么用"]),
        "关注售后": ("demand", ["售后", "服务", "保障", "培训", "维护"]),
        "关注案例": ("demand", ["案例", "客户", "同行", "成功", "效果"]),
    }
    objection_rules = {
        "价格异议": ["贵", "太高", "预算不够", "便宜", "优惠"],
        "周期异议": ["周期", "多久", "来不及", "上线时间"],
        "功能异议": ["不支持", "缺少", "做不了", "不满足"],
    }

    def analyze_messages(self, messages: list[dict]) -> ProfileResult:
        score = 50
        tags: list[ProfileTag] = []
        objection = ""
        demand = ""

        for message in messages:
            content = str(message.get("content") or "")
            if not message.get("from_customer", True):
                continue
            if "?" in content or "？" in content:
                score += 10
            if any(word in content for word in ["预算", "签约", "合同", "付款"]):
                score += 20
            if message.get("hours_ago", 9999) <= 24:
                score += 5
            if message.get("hours_ago", 0) >= 24 * 7:
                score -= 15

            for tag_name, (tag_type, keywords) in self.demand_rules.items():
                if any(keyword in content for keyword in keywords):
                    tags.append(ProfileTag(name=tag_name, type=tag_type))
                    demand = tag_name.replace("关注", "了解")

            for tag_name, keywords in self.objection_rules.items():
                if any(keyword in content for keyword in keywords):
                    tags.append(ProfileTag(name=tag_name, type="risk", confidence=0.85))
                    score += 10
                    objection = tag_name

        score = max(0, min(score, 100))
        return ProfileResult(
            intention_score=score,
            intention_level=self._score_to_level(score),
            tags=self._dedupe_profile_tags(tags),
            core_demand=demand or "待进一步确认",
            objection=objection,
        )

    def merge_tags(self, existing: list[dict], incoming: list[dict]) -> list[dict]:
        merged: dict[tuple[str, str], dict] = {}
        for item in existing + incoming:
            name = item.get("tag_name") or item.get("name")
            tag_type = item.get("tag_type") or item.get("type") or "demand"
            if not name:
                continue
            confidence = float(item.get("confidence", 1.0))
            key = (name, tag_type)
            current = merged.get(key)
            if current is None or confidence > current["confidence"]:
                merged[key] = {
                    "tag_name": name,
                    "tag_type": tag_type,
                    "source": item.get("source", "auto"),
                    "confidence": confidence,
                }
        return list(merged.values())

    def _dedupe_profile_tags(self, tags: list[ProfileTag]) -> list[ProfileTag]:
        merged = self.merge_tags(
            [],
            [{"tag_name": tag.name, "tag_type": tag.type, "source": tag.source, "confidence": tag.confidence} for tag in tags],
        )
        return [
            ProfileTag(name=item["tag_name"], type=item["tag_type"], source=item["source"], confidence=item["confidence"])
            for item in merged
        ]

    def _score_to_level(self, score: int) -> str:
        if score >= 80:
            return "S"
        if score >= 60:
            return "A"
        if score >= 40:
            return "B"
        if score >= 20:
            return "C"
        return "D"
