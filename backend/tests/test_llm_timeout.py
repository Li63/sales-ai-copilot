import asyncio

import pytest

from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_llm_service_returns_fallback_when_client_times_out(monkeypatch):
    async def slow_client(payload):
        await asyncio.sleep(0.02)
        return {}

    monkeypatch.setattr("app.services.llm_service.TEXT_MODEL_TIMEOUT_SECONDS", 0.01)
    service = LLMService(api_key="x", base_url="https://example.test", model="deepseek-chat", http_client=slow_client)

    result = await service.generate_sales_guide("test industry", "test customers", "test product")

    assert "test industry" in result
