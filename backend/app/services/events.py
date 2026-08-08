import asyncio
import json
import logging
from enum import Enum
from typing import Any

from fastapi import Request
from redis.asyncio import Redis

from app.services.cache import CacheService


logger = logging.getLogger(__name__)


class EventChannel(str, Enum):
    MEASUREMENTS = "smart-campus:measurements"
    ROOMS = "smart-campus:rooms"
    SENSORS = "smart-campus:sensors"
    EVENTS = "smart-campus:events"


class EventBus:
    def __init__(self, client: Redis | None, instance_id: str) -> None:
        self._client = client
        self._instance_id = instance_id

    async def publish(
        self,
        channel: EventChannel,
        event_type: str,
        payload: dict[str, Any] | None = None,
        cache_keys: list[str] | None = None,
        cache_patterns: list[str] | None = None,
    ) -> None:
        if self._client is None:
            return
        message = {
            "instance_id": self._instance_id,
            "type": event_type,
            "payload": payload or {},
            "cache_keys": cache_keys or [],
            "cache_patterns": cache_patterns or [],
        }
        try:
            await self._client.publish(channel.value, json.dumps(message))
        except Exception:
            logger.debug("Redis publish failed", exc_info=True)

    async def listen_for_cache_invalidation(
        self,
        cache: CacheService,
        stop_event: asyncio.Event,
    ) -> None:
        if self._client is None:
            return
        pubsub = self._client.pubsub(ignore_subscribe_messages=True)
        channels = [channel.value for channel in EventChannel]
        try:
            await pubsub.subscribe(*channels)
            while not stop_event.is_set():
                message = await pubsub.get_message(timeout=1.0)
                if not message:
                    continue
                await self._handle_message(message.get("data"), cache)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("Redis Pub/Sub listener stopped after an error", exc_info=True)
        finally:
            await pubsub.aclose()

    async def _handle_message(self, data: Any, cache: CacheService) -> None:
        if not isinstance(data, str):
            return
        try:
            message = json.loads(data)
        except json.JSONDecodeError:
            return
        if message.get("instance_id") == self._instance_id:
            return
        for key in message.get("cache_keys", []):
            if isinstance(key, str):
                await cache.delete(key)
        for pattern in message.get("cache_patterns", []):
            if isinstance(pattern, str):
                await cache.delete_pattern(pattern)


def get_event_bus(request: Request) -> EventBus:
    return request.app.state.event_bus
