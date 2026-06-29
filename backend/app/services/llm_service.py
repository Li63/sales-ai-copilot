import asyncio
import json
from collections.abc import Awaitable, Callable
from datetime import date
from typing import Any

import httpx


TEXT_MODEL_TIMEOUT_SECONDS = 12
VISION_MODEL_TIMEOUT_SECONDS = 25


SYSTEM_PROMPT = """你是这个行业里真正跑过一线、拿过结果的销冠型销售教练。你的任务不是写“AI 标准答案”，而是帮销售说出客户愿意听、听完愿意继续聊的话。
严格基于提供的对话内容分析，禁止编造未提及的信息。输出必须为标准 JSON 格式，不要任何额外解释。

回复风格要求：
1. 像真人销售，不要像客服模板，不要说“感谢您的咨询”“根据您的需求”这种空话。
2. 先接住客户情绪或顾虑，再给判断标准，最后轻轻推进下一步。
3. 要有温度、有分寸、有选择权，让客户感觉“你懂我”，而不是被逼成交。
4. 少用大道理，多用短句、口语、具体场景和低压提问。
5. 话术里可以有一点人味，比如“我理解你担心这个”“这个点确实得看清楚”“别急着定，我先帮你拆一下”。
6. 不夸大承诺，不装熟，不油腻，不强压客户。

字段：
- core_demand：客户当前核心诉求，15 字以内。
- objection：客户当前异议点，无则返回空字符串。
- reply_suggestions：数组，3 条推荐回复话术，每条不超过 110 字，可使用少量 Markdown 加粗重点。三条分别偏“稳重专业”“亲和共情”“引导提问”。
- reply_explanations：数组，3 条回复解析，必须和 reply_suggestions 一一对应，说明这条话术抓住客户什么点、为什么这样说。
- next_action：下一步跟进动作建议，20 字以内，可使用 Markdown 加粗重点。
- new_tags：本次对话新增的客户标签数组。
必须参考历史反馈复盘：如果类似话术得到差反馈，下次要换思路；如果类似话术得到好反馈，可以复用其底层逻辑。
客户公开资料只作为人设理解，不要编造客户未表达过的事实。"""


GUIDE_PROMPT = """你是该行业的顶尖销冠和销售训练师，既懂成交，也懂客户心理。
请根据销售填写的行业、目标客户群体和产品知识，生成一份可长期复用的销售指南。
要求：
1. 具体到该行业，不要写空泛内容。
2. 包含客户画像、购买动机、常见异议、破冰话术、推进步骤、跟进频率、成交信号、禁忌动作。
3. 输出 Markdown，结构清晰，重点内容使用 **加粗**，适合销售每天查看。
4. 语言务实、直接、可执行，但要像销冠在带徒弟：能讲透客户心里怎么想，也能告诉销售怎么自然开口。"""


IP_CONTENT_PROMPT = """你是销售个人 IP 内容策划教练，也是一名懂成交的内容操盘手。
请根据销售行业、客户群体、销售指南、主题和发布渠道，生成适合销售建立个人 IP 的内容。
要求：
1. 目标是建立专业、可信、有温度的人设，不要硬广。
2. 输出 Markdown。
3. 如果 channel 是 moments，输出标题、朋友圈正文、互动引导，正文控制在 180-350 字。
4. 如果 channel 是 douyin，输出短视频标题、3 秒开场钩子、分镜脚本、口播文案、字幕重点、结尾引导，口播控制在 45-90 秒。
5. 内容要贴合销售行业和目标客户，不要写泛泛鸡汤。
6. 文案要像真人销售自己的观察：有观点、有情绪、有细节，不要像公号模板。"""


DAILY_IP_PROMPT = """你是销售个人 IP 日更教练，擅长把行业观察写成销售能直接发的内容。
请基于当天日期、销售行业、客户群体和销售指南，给销售生成今天适合发朋友圈/自媒体的建议。
如果没有接入真实新闻源，不要编造具体新闻事件；可以输出今天可观察的热点方向、行业动态选题、客户关心角度、建议表达方式。
输出 Markdown，包含：
1. 今日内容方向
2. 行业热点切入角度
3. 客户可能关心的问题
4. 3 个可直接发布的选题
5. 1 条推荐朋友圈文案
语气要像销售本人在分享经验，有温度、有判断、有真实感，不要像 AI 总结。"""


INTENT_REPLY_PROMPT = """你是该行业顶尖销售教练，特别擅长把销售心里想推进的事，翻译成客户听着舒服、愿意接话的表达。
销售知道自己想推进什么，但不知道如何对客户表达。请结合客户画像、聊天历史、客户人设资料、公司资料、销售指南和历史反馈复盘，把销售的表达意图转成客户更容易接受的话术。
要求：
1. 站在客户视角判断这句话会不会有压迫感、会不会像硬推。
2. 必须贴合客户的聊天习惯、关注点、异议和人设资料。
3. 不能编造未出现的事实，不能承诺公司资料里没有的政策。
4. 话术要像真人销售发出去的微信：自然、短、有情绪承接、有选择权，不要像机器人。
5. 输出标准 JSON，不要 markdown 代码块。
字段：
- reply_suggestion：一条可直接发给客户的话术，120 字以内，可少量 Markdown 加粗重点。
- reply_explanation：说明这条话术抓住客户什么点、为什么这样讲，120 字以内。
- next_action：销售发完后下一步该观察或推进什么，40 字以内。
"""


PERSONA_ANALYSIS_PROMPT = """你是客户人设分析师，也是懂成交的一线销冠。
请根据客户公开资料、朋友圈/自媒体内容、抖音主页、抖音作品摘要、企查查类企业资料、聊天截图提取信息，给销售一份能立刻用于沟通的客户判断。

要求：
1. 严格基于输入资料，不编造客户身份、资产、关系、意向。
2. 先识别资料来源类型：douyin_profile、douyin_content、qichacha、website、manual。不同来源要用不同分析角度。
3. 抖音资料重点看内容定位、表达风格、评论/作品暴露出的关注点；企查查资料重点看经营范围、业务阶段、风险线索、组织变化。
4. 朋友圈/销售观察重点看真实性格、价值观、信任关系和沟通偏好；聊天记录重点看已经验证过的需求、预算、异议和成交阶段。
5. 所有判断都必须表达为“销售假设”，不能当成已验证事实。
6. 语言要像销售教练在提醒销售，务实、短句、可执行，不要像 AI 报告。
7. 对企业客户要做全方位解析：企业定位、实力证据、账号/人设、采购动机、成交机会、风险提醒、跟进策略、破冰话术。
8. 输出标准 JSON，不要 markdown 代码块。

字段：
- summary：客户资料透露出的核心判断，80 字以内。
- enterprise_positioning：企业做什么、卖给谁、处于什么业务场景，90 字以内。
- strength_evidence：资料里能证明企业实力或可信度的证据，90 字以内；没有证据要说证据不足。
- business_clues：经营状态、业务阶段或组织变化线索，80 字以内。
- content_positioning：抖音/公开内容呈现出的定位、表达风格或人设线索，80 字以内。
- communication_style：客户可能更接受的沟通方式，80 字以内。
- decision_logic：客户可能的判断标准或决策逻辑，80 字以内。
- purchase_motivation：客户可能的采购/合作动机或增长诉求，80 字以内。
- follow_angle：下一次可用的跟进角度，80 字以内。
- risk_warning：销售需要避免的动作或话术，80 字以内。
- sales_tip：一句给销售的实战提醒，80 字以内。
- deal_opportunity：从资料里能看出的潜在成交机会，80 字以内。
- customer_pain：客户可能正在意或害怕的痛点，80 字以内。
- follow_strategy：下一轮跟进策略，包含节奏和切入点，80 字以内。
- icebreaker：一条销售可以直接发出的低压破冰话术，100 字以内。
"""

PERSONA_IMAGE_ANALYSIS_PROMPT = """你是客户截图情报分析师，也是懂成交的一线销冠。
销售上传的多数资料是截图：抖音主页、抖音作品、评论区、朋友圈、企查查、官网、聊天记录。你的任务是直接看图，不要只做 OCR。

要求：
1. 同时利用图片内容、图片版式、销售补充文字、来源链接和客户已有资料。
2. 先判断截图类型：抖音主页、抖音作品、评论区、朋友圈、企查查、官网、聊天记录、其他。
3. 区分“可确认事实”和“销售假设”；不要把截图里没有的信息当事实。
4. 抖音看账号定位、作品场景、评论痛点和获客方式；朋友圈看真实性格、信任偏好和关系温度；企查查看企业真实经营、规模、风险和实力证据。
5. 对企业客户输出能直接指导销售的全方位解析。
6. 输出标准 JSON，不要 markdown 代码块。

字段：
- summary：截图透露出的核心判断，80 字以内。
- screenshot_type：截图类型，20 字以内。
- confirmed_facts：截图中可以确认的事实，100 字以内。
- sales_hypothesis：基于截图形成的销售假设，100 字以内。
- enterprise_positioning：企业做什么、卖给谁、处于什么业务场景，90 字以内。
- strength_evidence：资料里能证明企业实力或可信度的证据，90 字以内；没有证据要说证据不足。
- business_clues：经营状态、业务阶段或组织变化线索，80 字以内。
- content_positioning：抖音/公开内容呈现出的定位、表达风格或人设线索，80 字以内。
- communication_style：客户可能更接受的沟通方式，80 字以内。
- decision_logic：客户可能的判断标准或决策逻辑，80 字以内。
- purchase_motivation：客户可能的采购/合作动机或增长诉求，80 字以内。
- deal_opportunity：从截图能看出的潜在成交机会，80 字以内。
- customer_pain：客户可能正在意或害怕的痛点，80 字以内。
- risk_warning：销售需要避免的动作或话术，80 字以内。
- follow_strategy：下一轮跟进策略，包含节奏和切入点，80 字以内。
- icebreaker：一条销售可以直接发出的低压破冰话术，100 字以内。
- missing_evidence：还缺哪些截图或资料，80 字以内。
"""


VISION_PROMPTS = {
    "chat": "请识别这些聊天截图中的文字，按时间顺序整理成“客户：... / 销售：...”格式。只输出可用于销售分析的文本，不要编造看不清的内容。",
    "persona": "请识别这些客户朋友圈、自媒体或公开资料截图，提取能体现客户身份、兴趣、业务状态、近期关注点和沟通偏好的信息。输出结构化中文要点。",
    "company": "请识别这些公司资料、产品、报价、案例或售后政策图片，提取可用于销售回复的关键信息。输出结构化中文要点。",
}


class LLMService:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        vision_api_key: str = "",
        vision_base_url: str = "",
        vision_model: str = "",
        http_client: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]] | None = None,
        vision_http_client: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]] | None = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.vision_api_key = vision_api_key or api_key
        self.vision_base_url = (vision_base_url or base_url).rstrip("/")
        self.vision_model = vision_model or model
        self.http_client = http_client or self._post_chat_completion
        self.vision_http_client = vision_http_client or self._post_vision_completion

    async def generate_sales_guide(self, industry: str, customer_group: str, product_knowledge: str) -> str:
        payload = self._payload(
            GUIDE_PROMPT,
            {
                "industry": industry,
                "customer_group": customer_group,
                "product_knowledge": product_knowledge,
            },
            temperature=0.35,
        )
        try:
            response = await self._call_text_model(payload)
            return str(response["choices"][0]["message"]["content"]).strip()
        except Exception:
            return self.fallback_guide(industry, customer_group)

    async def analyze_realtime(
        self,
        customer_profile: dict[str, Any],
        chat_history: list[dict[str, Any]],
        product_knowledge: str,
        sales_guide: str = "",
        memory_summary: str = "",
        feedback_lessons: list[dict[str, Any]] | None = None,
        persona_sources: list[dict[str, Any]] | None = None,
        sales_playbook: str = "",
    ) -> dict[str, Any]:
        payload = self._payload(
            SYSTEM_PROMPT,
            {
                "customer_profile": customer_profile,
                "chat_history": chat_history[:20],
                "product_knowledge": product_knowledge,
                "sales_guide": sales_guide,
                "memory_summary": memory_summary,
                "global_feedback_lessons": feedback_lessons or [],
                "customer_persona_sources": persona_sources or [],
                "shared_sales_playbook": sales_playbook,
                "analysis_angle": "同时站在该行业顶尖销售和客户视角，给出更像真人销冠的跟进节奏、回复逻辑与下一步动作。先接情绪，再拆判断标准，最后轻推进。",
            },
            temperature=0.3,
        )
        try:
            response = await self._call_text_model(payload)
            content = response["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return self._normalize(parsed)
        except Exception:
            return self.fallback(chat_history)

    async def generate_intent_reply(
        self,
        intent: str,
        customer_profile: dict[str, Any],
        chat_history: list[dict[str, Any]],
        product_knowledge: str,
        sales_guide: str = "",
        memory_summary: str = "",
        feedback_lessons: list[dict[str, Any]] | None = None,
        persona_sources: list[dict[str, Any]] | None = None,
        sales_playbook: str = "",
    ) -> dict[str, str]:
        payload = self._payload(
            INTENT_REPLY_PROMPT,
            {
                "sales_intent": intent,
                "customer_profile": customer_profile,
                "chat_history": chat_history[:20],
                "product_knowledge": product_knowledge,
                "sales_guide": sales_guide,
                "memory_summary": memory_summary,
                "global_feedback_lessons": feedback_lessons or [],
                "customer_persona_sources": persona_sources or [],
                "shared_sales_playbook": sales_playbook,
            },
            temperature=0.42,
        )
        try:
            response = await self._call_text_model(payload)
            parsed = json.loads(response["choices"][0]["message"]["content"])
            return {
                "reply_suggestion": str(parsed.get("reply_suggestion", ""))[:220],
                "reply_explanation": str(parsed.get("reply_explanation", ""))[:260],
                "next_action": str(parsed.get("next_action", ""))[:120],
            }
        except Exception:
            return self.fallback_intent_reply(intent, customer_profile)

    async def analyze_persona_source(
        self,
        content: str,
        customer_profile: dict[str, Any] | None = None,
        source_type: str = "manual",
        source_url: str = "",
    ) -> str:
        payload = self._payload(
            PERSONA_ANALYSIS_PROMPT,
            {
                "customer_profile": customer_profile or {},
                "source_type": source_type,
                "source_url": source_url,
                "persona_source_content": content[:5000],
            },
            temperature=0.25,
        )
        try:
            response = await self._call_text_model(payload)
            parsed = json.loads(response["choices"][0]["message"]["content"])
            return self._format_persona_analysis(parsed)
        except Exception:
            return self.fallback_persona_analysis(content, source_type=source_type, source_url=source_url)

    async def analyze_persona_images(
        self,
        images: list[dict[str, str]],
        customer_profile: dict[str, Any] | None = None,
        source_type: str = "manual",
        source_url: str = "",
        text_context: str = "",
    ) -> str:
        if not images:
            return self.fallback_persona_analysis(text_context, source_type=source_type, source_url=source_url)
        context = {
            "customer_profile": customer_profile or {},
            "source_type": source_type,
            "source_url": source_url,
            "sales_text_context": text_context[:4000],
            "analysis_warning": "请直接看截图做判断；不要只复述 OCR。无法从截图确认的信息必须写成销售假设或缺失证据。",
        }
        content: list[dict[str, Any]] = [
            {"type": "text", "text": f"{PERSONA_IMAGE_ANALYSIS_PROMPT}\n\n上下文：{json.dumps(context, ensure_ascii=False)}"}
        ]
        for image in images[:6]:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{image['content_type']};base64,{image['base64']}"},
                }
            )
        payload = {
            "model": self.vision_model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.18,
        }
        try:
            response = await asyncio.wait_for(self.vision_http_client(payload), timeout=VISION_MODEL_TIMEOUT_SECONDS)
            parsed = json.loads(response["choices"][0]["message"]["content"])
            return self._format_persona_analysis(parsed)
        except Exception:
            image_names = "、".join(image.get("filename", "截图") for image in images[:6])
            fallback_content = (
                f"截图已上传：{image_names}\n"
                f"销售补充：{text_context}\n"
                "视觉模型暂时未返回结构化结果，只能先作为待验证截图资料。"
            )
            return self.fallback_persona_analysis(fallback_content, source_type=source_type, source_url=source_url)

    async def generate_ip_content(
        self,
        industry: str,
        customer_group: str,
        sales_guide: str,
        theme: str,
        channel: str = "moments",
    ) -> str:
        payload = self._payload(
            IP_CONTENT_PROMPT,
            {
                "industry": industry,
                "customer_group": customer_group,
                "sales_guide": sales_guide,
                "theme": theme,
                "channel": channel,
            },
            temperature=0.45,
        )
        try:
            response = await self._call_text_model(payload)
            return str(response["choices"][0]["message"]["content"]).strip()
        except Exception:
            return self.fallback_ip_content(industry, customer_group, theme, channel)

    async def generate_daily_ip_advice(self, industry: str, customer_group: str, sales_guide: str) -> str:
        today = date.today().isoformat()
        payload = self._payload(
            DAILY_IP_PROMPT,
            {
                "date": today,
                "industry": industry,
                "customer_group": customer_group,
                "sales_guide": sales_guide,
                "news_source_status": "当前未接入实时新闻源 API，请不要编造具体新闻，只给可观察方向和稳定内容建议。",
            },
            temperature=0.4,
        )
        try:
            response = await self._call_text_model(payload)
            return str(response["choices"][0]["message"]["content"]).strip()
        except Exception:
            return self.fallback_daily_ip_advice(industry, customer_group, today)

    async def analyze_images(self, images: list[dict[str, str]], purpose: str = "chat") -> str:
        if not images:
            return ""
        prompt = VISION_PROMPTS.get(purpose, VISION_PROMPTS["chat"])
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for image in images[:6]:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{image['content_type']};base64,{image['base64']}"},
                }
            )
        payload = {
            "model": self.vision_model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.1,
        }
        try:
            response = await asyncio.wait_for(self.vision_http_client(payload), timeout=VISION_MODEL_TIMEOUT_SECONDS)
            return str(response["choices"][0]["message"]["content"]).strip()
        except Exception:
            filenames = "、".join(image.get("filename", "图片") for image in images)
            return f"图片已上传：{filenames}。视觉模型暂时未返回内容，请手动补充图片中的关键文字。"

    def _payload(self, system_prompt: str, data: dict[str, Any], temperature: float) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(data, ensure_ascii=False)},
            ],
            "temperature": temperature,
        }

    async def _call_text_model(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.wait_for(self.http_client(payload), timeout=TEXT_MODEL_TIMEOUT_SECONDS)

    async def _post_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key or not self.base_url:
            raise RuntimeError("LLM_API_KEY and LLM_BASE_URL are required")
        async with httpx.AsyncClient(timeout=TEXT_MODEL_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def _post_vision_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.vision_api_key or not self.vision_base_url:
            raise RuntimeError("VISION_API_KEY/VISION_BASE_URL or LLM_API_KEY/LLM_BASE_URL are required")
        async with httpx.AsyncClient(timeout=VISION_MODEL_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{self.vision_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.vision_api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    def fallback_guide(self, industry: str, customer_group: str) -> str:
        return f"""# {industry or '当前行业'}销售指南

## 目标客户
面向：**{customer_group or '待明确客户群体'}**

## 核心打法
1. 先确认客户现状、预算、决策链和时间节点。
2. 用案例证明效果，再讨论价格。
3. 每次沟通都留下一个明确的下一步动作。

## 跟进频率
- **高意向**：当天跟进，24 小时内推进下一步。
- **中意向**：2-3 天一次，围绕案例、方案、预算推进。
- **低意向**：每 7 天轻触达一次，提供行业资料或客户案例。
"""

    def fallback_ip_content(self, industry: str, customer_group: str, theme: str, channel: str = "moments") -> str:
        if channel == "douyin":
            return f"""# {theme or '销售短视频选题'}

## 3 秒开场钩子
客户一上来就问价格，你千万别急着报价。

## 分镜脚本
- **镜头 1**：销售面对镜头，提出客户常见问题。
- **镜头 2**：拆解客户真正担心的是投入风险，而不只是价格。
- **镜头 3**：给出一个判断方案是否靠谱的简单标准。

## 口播文案
很多{customer_group or '客户'}问价格，并不是只想找便宜，而是在判断这件事值不值得投入。

如果你是做{industry or '这个行业'}销售，先别急着报最低价。可以先问客户三个问题：现在最卡的地方是什么？这个问题拖下去会损失什么？客户希望方案解决到什么程度？

当客户把判断标准说清楚，价格才有讨论空间，成交也更自然。

## 字幕重点
客户问价 = 在判断风险
先问场景，再讲方案
报价前先建立判断标准

## 结尾引导
你遇到过客户只问价格的情况吗？评论区说说。
"""
        return f"""# {theme or industry or '今日销售观察'}

很多客户一开始问价格，其实背后更关心的是：**这件事值不值得投入**。

如果你也是{customer_group or '正在评估方案的客户'}，建议先想清楚三个问题：

- 当前最卡你的问题是什么？
- 这个问题拖下去会带来什么损失？
- 什么样的方案才算真正解决问题？

专业销售不应该只催成交，而是帮客户把判断标准变清楚。

你最近在决策时最纠结的问题是什么？
"""

    def fallback_daily_ip_advice(self, industry: str, customer_group: str, today: str) -> str:
        return f"""# {today} 今日 IP 建议

## 今日内容方向
围绕 **{industry or '你的行业'}里的客户决策误区** 发一条专业但不硬广的内容。

## 行业热点切入角度
不追未经确认的新闻，优先讲客户每天都会遇到的真实问题：预算、效果、风险、交付、售后。

## 客户可能关心的问题
{customer_group or '目标客户'}通常更关心：**投入是否值得、选择是否有风险、有没有同行经验**。

## 可发布选题
- 为什么客户问价格时，真正想确认的是风险？
- 一个靠谱方案，应该先讲效果还是先讲报价？
- 判断服务值不值，别只看一次性成本。

## 推荐朋友圈文案
客户问价格并不是坏事，说明他已经开始认真评估。

真正专业的沟通，不是急着报价，而是先把**需求、风险、投入产出**讲清楚。
"""

    def fallback_intent_reply(self, intent: str, customer_profile: dict[str, Any]) -> dict[str, str]:
        demand = customer_profile.get("core_demand") or "当前关注点"
        objection = customer_profile.get("objection") or "顾虑"
        return {
            "reply_suggestion": f"这个点我理解，您现在主要还是想把**{demand}**看清楚。关于{intent[:60]}，我不想硬推您，先帮您拆成几个判断点，您看完再决定要不要往下聊。",
            "reply_explanation": f"先承认客户顾虑，再把销售目的包装成客户可判断的标准，压迫感会小很多。",
            "next_action": f"看客户是否继续追问{objection}",
        }

    def fallback_persona_analysis(self, content: str, source_type: str = "manual", source_url: str = "") -> str:
        text = content.strip().replace("\n", " ")
        if not text:
            return ""
        clue = text[:120]
        return (
            f"资料来源：{source_type}{f'（{source_url}）' if source_url else ''}\n"
            f"核心判断：客户公开资料显示：{clue}\n"
            "企业定位：资料有限，先判断其公开业务方向和服务对象，不能扩大解读。\n"
            "实力证据：当前只看到用户提供的资料线索，企业规模、产能、资质仍需企查查或官网验证。\n"
            "经营线索：资料有限，先把它作为销售假设，不直接下结论。\n"
            "内容定位：若来自抖音或公开主页，优先观察其表达风格、案例主题和评论里的真实顾虑。\n"
            "决策逻辑：先用资料里的真实线索确认客户现在是否仍关注这件事。\n"
            "采购动机：可能围绕获客、效率、交付稳定或风险降低，但需要进一步确认。\n"
            "沟通方式：先围绕资料里出现的真实关注点开口，少用模板化寒暄。\n"
            "跟进角度：用一个低压问题确认客户当前是否还在关注这件事。\n"
            "风险提醒：不要把单次资料当成最终结论，也不要直接推产品。\n"
            "销售提醒：先让客户感觉你看懂了他，再轻轻推进下一步。\n"
            "成交机会：资料里出现的业务变化、内容方向或公开动作，可能是切入合作的窗口。\n"
            "客户痛点：客户可能在意效果、风险、可信证据或交付稳定性，需先验证再推进。\n"
            "跟进策略：先用资料里的真实线索破冰，再问一个低压问题确认当前优先级。\n"
            "破冰话术：我看到您最近在关注这个方向，我不确定现在是不是重点，想先和您确认一个小问题。"
        )

    def _format_persona_analysis(self, parsed: dict[str, Any]) -> str:
        lines = [
            ("核心判断", parsed.get("summary", "")),
            ("截图类型", parsed.get("screenshot_type", "")),
            ("可确认事实", parsed.get("confirmed_facts", "")),
            ("销售假设", parsed.get("sales_hypothesis", "")),
            ("企业定位", parsed.get("enterprise_positioning", "")),
            ("实力证据", parsed.get("strength_evidence", "")),
            ("经营线索", parsed.get("business_clues", "")),
            ("内容定位", parsed.get("content_positioning", "")),
            ("沟通方式", parsed.get("communication_style", "")),
            ("决策逻辑", parsed.get("decision_logic", "")),
            ("采购动机", parsed.get("purchase_motivation", "")),
            ("跟进角度", parsed.get("follow_angle", "")),
            ("风险提醒", parsed.get("risk_warning", "")),
            ("销售提醒", parsed.get("sales_tip", "")),
            ("成交机会", parsed.get("deal_opportunity", "")),
            ("客户痛点", parsed.get("customer_pain", "")),
            ("跟进策略", parsed.get("follow_strategy", "")),
            ("破冰话术", parsed.get("icebreaker", "")),
            ("缺失证据", parsed.get("missing_evidence", "")),
        ]
        return "\n".join(f"{label}：{str(value).strip()[:140]}" for label, value in lines if str(value).strip())

    def fallback(self, chat_history: list[dict[str, Any]]) -> dict[str, Any]:
        text = " ".join(str(item.get("content", "")) for item in chat_history[:5])
        price_related = any(word in text for word in ["价格", "报价", "费用", "优惠", "预算", "贵"])
        demand = "了解价格" if price_related else "确认需求"
        objection = "价格异议" if any(word in text for word in ["贵", "预算", "便宜"]) else ""
        suggestions = [
            "价格这个点确实得看清楚。我先按您的情况拆一下**费用构成**，您也好判断这笔投入值不值。",
            "我理解您担心成本，咱们别急着定高低，先看**哪种方案最适合您现在这个阶段**。",
            "我想先确认一下，您现在更卡的是一次性价格，还是担心后面用起来的**整体投入产出**？",
        ]
        return {
            "core_demand": demand,
            "objection": objection,
            "reply_suggestions": suggestions,
            "reply_explanations": [
                "先承认价格需要看清楚，再拆费用，客户会感觉你是在帮他判断，不是在催他买。",
                "先共情成本压力，再把讨论拉回阶段适配，避免直接陷入砍价。",
                "用低压问题把客户从价格拉到投入产出，后续更容易讲价值。",
            ],
            "next_action": "确认预算与场景",
            "new_tags": ["价格敏感"] if price_related else ["待确认需求"],
        }

    def _normalize(self, parsed: dict[str, Any]) -> dict[str, Any]:
        fallback = self.fallback([])
        suggestions = parsed.get("reply_suggestions") or []
        if isinstance(suggestions, str):
            suggestions = [suggestions]
        suggestions = (suggestions + fallback["reply_suggestions"])[:3]

        explanations = parsed.get("reply_explanations") or []
        if isinstance(explanations, str):
            explanations = [explanations]
        explanations = (explanations + fallback["reply_explanations"])[:3]

        tags = []
        for item in parsed.get("new_tags", [])[:10]:
            if isinstance(item, dict):
                name = item.get("tag_name") or item.get("name") or item.get("label")
                if name:
                    tags.append(str(name)[:32])
            else:
                tags.append(str(item)[:32])
        return {
            "core_demand": str(parsed.get("core_demand", ""))[:30],
            "objection": str(parsed.get("objection", ""))[:80],
            "reply_suggestions": [str(item)[:180] for item in suggestions],
            "reply_explanations": [str(item)[:220] for item in explanations],
            "next_action": str(parsed.get("next_action", ""))[:80],
            "new_tags": tags,
        }
