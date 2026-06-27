from app.services.profile_engine import ProfileEngine


def test_profile_engine_scores_budget_and_question_as_high_intent():
    engine = ProfileEngine()

    result = engine.analyze_messages(
        [
            {"from_customer": True, "content": "你们价格是多少？如果预算合适这周可以签约吗？", "hours_ago": 1},
            {"from_customer": True, "content": "售后怎么保障？有没有案例？", "hours_ago": 2},
        ]
    )

    assert result.intention_score >= 80
    assert result.intention_level == "S"
    assert "关注价格" in [tag.name for tag in result.tags]
    assert "关注售后" in [tag.name for tag in result.tags]


def test_profile_engine_penalizes_inactive_customer():
    engine = ProfileEngine()

    result = engine.analyze_messages(
        [{"from_customer": True, "content": "先了解一下", "hours_ago": 24 * 9}]
    )

    assert result.intention_level in {"B", "C", "D"}
    assert result.intention_score < 60


def test_merge_tags_deduplicates_and_keeps_highest_confidence():
    engine = ProfileEngine()

    merged = engine.merge_tags(
        existing=[{"tag_name": "关注价格", "tag_type": "demand", "confidence": 0.6}],
        incoming=[{"tag_name": "关注价格", "tag_type": "demand", "confidence": 0.9}],
    )

    assert len(merged) == 1
    assert merged[0]["confidence"] == 0.9
