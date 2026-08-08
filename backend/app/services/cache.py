import json
from datetime import date, datetime
from typing import Any

from fastapi import Request
from pydantic import BaseModel
from redis.asyncio import Redis


def _json_default(value: Any) -> str:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class CacheService:
    def __init__(self, client: Redis | None, default_ttl_seconds: int) -> None:
        self._client = client
        self._default_ttl_seconds = default_ttl_seconds

    async def get_json(self, key: str) -> Any | None:
        if self._client is None:
            return None
        try:
            raw_value = await self._client.get(key)
        except Exception:
            return None
        if raw_value is None:
            return None
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return None

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        if self._client is None:
            return
        try:
            await self._client.set(
                key,
                json.dumps(value, default=_json_default),
                ex=ttl_seconds or self._default_ttl_seconds,
            )
        except Exception:
            return

    async def delete(self, *keys: str) -> None:
        if self._client is None or not keys:
            return
        try:
            await self._client.delete(*keys)
        except Exception:
            return

    async def delete_pattern(self, pattern: str) -> None:
        if self._client is None:
            return
        try:
            keys = [key async for key in self._client.scan_iter(match=pattern)]
            if keys:
                await self._client.delete(*keys)
        except Exception:
            return


def get_cache_service(request: Request) -> CacheService:
    return request.app.state.cache_service
