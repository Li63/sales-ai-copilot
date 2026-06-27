import pytest

from app.services.wecom_client import WeComClient


class MemoryCache:
    def __init__(self):
        self.values = {}

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, ex=None):
        self.values[key] = value


@pytest.mark.asyncio
async def test_access_token_is_cached_by_secret_name():
    calls = []

    async def http_get(url, params):
        calls.append(params["corpsecret"])
        return {"errcode": 0, "access_token": f"token-{len(calls)}", "expires_in": 7200}

    client = WeComClient(corp_id="corp", cache=MemoryCache(), http_get=http_get)

    first = await client.get_access_token("app", "secret-a")
    second = await client.get_access_token("app", "secret-a")
    archive = await client.get_access_token("archive", "secret-b")

    assert first == "token-1"
    assert second == "token-1"
    assert archive == "token-2"
    assert calls == ["secret-a", "secret-b"]
