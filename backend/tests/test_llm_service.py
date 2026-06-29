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


@pytest.mark.asyncio
async def test_llm_service_generates_persona_analysis_for_sales():
    captured = {}

    async def ok_client(payload):
        captured.update(payload)
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"summary":"客户近期在扩团队，重视交付稳定性。","communication_style":"喜欢直接看结论和案例，不喜欢被催。","follow_angle":"先给同行案例，再轻问当前推进卡点。","risk_warning":"不要一上来压成交或连续追问预算。","sales_tip":"用短句确认标准，让客户觉得你在帮他把风险看清楚。"}'
                    }
                }
            ]
        }

    service = LLMService(api_key="x", base_url="https://example.test", model="deepseek-chat", http_client=ok_client)

    result = await service.analyze_persona_source(
        "朋友圈提到最近扩团队，正在比较供应商，担心服务跟不上。",
        customer_profile={"nickname": "王总", "core_demand": "比较供应商"},
    )

    assert captured["messages"][0]["role"] == "system"
    assert "客户人设分析师" in captured["messages"][0]["content"]
    assert "扩团队" in result
    assert "跟进角度" in result
    assert "销售提醒" in result


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


@pytest.mark.asyncio
async def test_llm_persona_formats_enterprise_battle_fields():
    async def ok_client(payload):
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"summary":"客户是食品机械设备厂家。","enterprise_positioning":"面向果蔬加工客户销售切条切片设备。","strength_evidence":"以设备实拍、工厂身份和细分产品标签建立可信度。","purchase_motivation":"可能更关注获客线索、设备询盘和经销合作。","deal_opportunity":"可从萝卜切条机细分场景切入，聊批量客户需求。","customer_pain":"需要证明设备稳定、效率和售后能力。","follow_strategy":"先围绕视频里的具体设备场景提问，再补同行案例。","icebreaker":"我看到您在发萝卜切条机这类细分设备，想请教下现在客户更关心效率还是售后稳定？"}'
                    }
                }
            ]
        }

    service = LLMService(api_key="x", base_url="https://example.test", model="deepseek-chat", http_client=ok_client)

    result = await service.analyze_persona_source(
        "平台：抖音\n账号：金林食品机械设备厂家\n作品线索：瓜果蔬菜萝卜切条机\n标签：萝卜切条机、果蔬推条机",
        source_type="douyin_content",
        source_url="https://v.douyin.com/VhrrmUHw3SM/",
    )

    assert "企业定位：面向果蔬加工客户销售切条切片设备。" in result
    assert "实力证据：以设备实拍、工厂身份和细分产品标签建立可信度。" in result
    assert "采购动机：可能更关注获客线索、设备询盘和经销合作。" in result
    assert "破冰话术：我看到您在发萝卜切条机这类细分设备" in result
