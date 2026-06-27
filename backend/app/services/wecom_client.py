import hashlib
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.core.cache import AsyncCache


class WeComClient:
    base_url = "https://qyapi.weixin.qq.com"

    def __init__(
        self,
        corp_id: str,
        cache: AsyncCache,
        http_get: Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]] | None = None,
        http_post: Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]] | None = None,
    ):
        self.corp_id = corp_id
        self.cache = cache
        self.http_get = http_get or self._http_get
        self.http_post = http_post or self._http_post

    async def get_access_token(self, secret_name: str, secret: str) -> str:
        cache_key = f"wecom:access_token:{secret_name}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        data = await self.http_get(
            f"{self.base_url}/cgi-bin/gettoken",
            {"corpid": self.corp_id, "corpsecret": secret},
        )
        if data.get("errcode") != 0:
            raise RuntimeError(f"WeCom token error: {data}")
        token = data["access_token"]
        await self.cache.set(cache_key, token, ex=max(int(data.get("expires_in", 7200)) - 300, 60))
        return token

    async def get_jsapi_ticket(self, access_token: str) -> str:
        cache_key = "wecom:jsapi_ticket"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        data = await self.http_get(
            f"{self.base_url}/cgi-bin/get_jsapi_ticket",
            {"access_token": access_token},
        )
        if data.get("errcode") != 0:
            raise RuntimeError(f"WeCom jsapi ticket error: {data}")
        ticket = data["ticket"]
        await self.cache.set(cache_key, ticket, ex=max(int(data.get("expires_in", 7200)) - 300, 60))
        return ticket

    async def list_external_contacts(self, access_token: str, userid: str) -> list[str]:
        data = await self.http_get(
            f"{self.base_url}/cgi-bin/externalcontact/list",
            {"access_token": access_token, "userid": userid},
        )
        if data.get("errcode") != 0:
            raise RuntimeError(f"WeCom external contact list error: {data}")
        return data.get("external_userid", [])

    async def get_external_contact(self, access_token: str, external_userid: str) -> dict[str, Any]:
        data = await self.http_get(
            f"{self.base_url}/cgi-bin/externalcontact/get",
            {"access_token": access_token, "external_userid": external_userid},
        )
        if data.get("errcode") != 0:
            raise RuntimeError(f"WeCom external contact get error: {data}")
        return data

    async def get_user_info_by_code(self, access_token: str, code: str) -> dict[str, Any]:
        data = await self.http_get(
            f"{self.base_url}/cgi-bin/auth/getuserinfo",
            {"access_token": access_token, "code": code},
        )
        if data.get("errcode") != 0:
            raise RuntimeError(f"WeCom auth error: {data}")
        return data

    def build_js_sdk_signature(self, ticket: str, nonce_str: str, timestamp: int, url: str) -> dict[str, Any]:
        raw = f"jsapi_ticket={ticket}&noncestr={nonce_str}&timestamp={timestamp}&url={url}"
        return {
            "corpId": self.corp_id,
            "timestamp": timestamp,
            "nonceStr": nonce_str,
            "signature": hashlib.sha1(raw.encode("utf-8")).hexdigest(),
        }

    async def _http_get(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def _http_post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()


def now_timestamp() -> int:
    return int(time.time())
