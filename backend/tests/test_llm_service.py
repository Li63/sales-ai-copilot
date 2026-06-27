import pytest

from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_llm_service_returns_fallback_when_client_fails():
    async def failing_client(payload):
        raise RuntimeError("upstream unavailable")

    service = LLMService(api_key="", base_url="", model="deepseek-chat", http_client=failing_client)

    result = await service.analyze_realtime(
        customer_profile={"nickname": "张三", "intention_level": "A"},
        chat_history=[{"content": "价格有点贵，能优惠吗？"}],
        product_knowledge="标准产品包",
    )

    assert result["core_demand"] == "了解价格"
    assert result["objection"] == "价格异议"
    assert len(result["reply_suggestions"]) == 3
    assert len(result["reply_explanations"]) == 3
    assert "价格敏感" in result["new_tags"]


@pytest.mark.asyncio
async def test_llm_service_parses_openai_compatible_json_content():
    async def ok_client(payload):
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"core_demand":"看案例","objection":"","reply_suggestions":["专业回复","亲和回复","提问回复"],"reply_explanations":["抓案例点","先拉近","再提问"],"next_action":"发送案例","new_tags":["关注案例"]}'
                    }
                }
            ]
        }

    service = LLMService(api_key="x", base_url="https://example.test", model="deepseek-chat", http_client=ok_client)

    result = await service.analyze_realtime({}, [], "")

    assert result["core_demand"] == "看案例"
    assert result["reply_explanations"][0] == "抓案例点"
    assert result["next_action"] == "发送案例"
    assert result["new_tags"] == ["关注案例"]


@pytest.mark.asyncio
async def test_llm_service_normalizes_string_suggestions_and_object_tags():
    async def odd_client(payload):
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"core_demand":"了解案例","objection":"","reply_suggestions":"先回应**案例需求**，再追问行业","reply_explanations":"抓住客户要案例的信号","next_action":"发送案例","new_tags":[{"tag_name":"关注案例"}]}'
                    }
                }
            ]
        }

    service = LLMService(api_key="x", base_url="https://example.test", model="deepseek-chat", http_client=odd_client)

    result = await service.analyze_realtime({}, [], "")

    assert result["reply_suggestions"][0] == "先回应**案例需求**，再追问行业"
    assert result["reply_explanations"][0] == "抓住客户要案例的信号"
    assert len(result["reply_suggestions"]) == 3
    assert result["new_tags"] == ["关注案例"]


@pytest.mark.asyncio
async def test_llm_service_sends_vision_payload_with_image_url_content():
    captured = {}

    async def ok_client(payload):
        captured.update(payload)
        return {"choices": [{"message": {"content": "客户：想了解价格\n销售：我给您拆一下费用"}}]}

    service = LLMService(
        api_key="x",
        base_url="https://example.test",
        model="text-model",
        vision_api_key="vx",
        vision_base_url="https://vision.example.test",
        vision_model="vision-model",
        vision_http_client=ok_client,
    )

    result = await service.analyze_images(
        [{"filename": "chat.png", "content_type": "image/png", "base64": "ZmFrZQ=="}],
        purpose="chat",
    )

    assert captured["model"] == "vision-model"
    assert captured["messages"][0]["content"][0]["type"] == "text"
    assert captured["messages"][0]["content"][1]["type"] == "image_url"
    assert captured["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert "客户：想了解价格" in result
