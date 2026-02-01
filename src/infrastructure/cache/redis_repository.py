from __future__ import annotations

from redis.asyncio import Redis


class RedisCache:
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        value = await self._client.get(key)
        return value.decode("utf-8") if value else None

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        await self._client.set(key, value, ex=ttl)

