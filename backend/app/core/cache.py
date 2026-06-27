import time
from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings


class AsyncCache:
    async def get(self, key: str) -> str | None:
        raise NotImplementedError

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        raise NotImplementedError


class RedisCache(AsyncCache):
    def __init__(self, url: str):
        self.client = redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        await self.client.set(key, value, ex=ex)


class MemoryCache(AsyncCache):
    def __init__(self):
        self.values: dict[str, tuple[str, float | None]] = {}

    async def get(self, key: str) -> str | None:
        item = self.values.get(key)
        if item is None:
            return None
        value, expires_at = item
        if expires_at is not None and expires_at < time.time():
            self.values.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        expires_at = time.time() + ex if ex else None
        self.values[key] = (value, expires_at)


_memory_cache = MemoryCache()


def get_cache() -> AsyncCache:
    settings = get_settings()
    if settings.environment == "local":
        return _memory_cache
    return RedisCache(settings.redis_url)
