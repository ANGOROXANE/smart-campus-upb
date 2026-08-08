import json

import pytest

from app.models.room import Room, RoomCreate
from app.models.sensor import Sensor
from app.services.cache import CacheService
from app.services.catalog import CatalogService, ROOMS_CACHE_KEY
from app.services.events import EventBus, EventChannel
from app.services.rate_limit import RateLimiter


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.expirations: dict[str, int] = {}
        self.deleted: list[str] = []
        self.published: list[tuple[str, str]] = []

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int) -> None:
        self.values[key] = value
        self.expirations[key] = ex

    async def delete(self, *keys: str) -> None:
        self.deleted.extend(keys)
        for key in keys:
            self.values.pop(key, None)

    async def scan_iter(self, match: str):
        prefix = match.rstrip("*")
        for key in list(self.values):
            if key.startswith(prefix):
                yield key

    async def publish(self, channel: str, message: str) -> None:
        self.published.append((channel, message))

    async def incr(self, key: str) -> int:
        current = int(self.values.get(key, "0")) + 1
        self.values[key] = str(current)
        return current

    async def expire(self, key: str, seconds: int) -> None:
        self.expirations[key] = seconds

    async def ttl(self, key: str) -> int:
        return self.expirations.get(key, -1)


class FakeRepository:
    def __init__(self) -> None:
        self.rooms = [Room(id="room-1", name="A101", building="A", floor=1, capacity=40)]
        self.list_calls = 0

    async def list_rooms(self) -> list[Room]:
        self.list_calls += 1
        return self.rooms

    async def create_room(self, room: RoomCreate) -> Room:
        created = Room(id="room-2", **room.model_dump())
        self.rooms.append(created)
        return created

    async def list_sensors(self) -> list[Sensor]:
        return []


class FakeRequest:
    def __init__(self, path: str = "/rooms", authorization: str | None = None) -> None:
        self.url = type("Url", (), {"path": path})()
        self.headers = {"authorization": authorization} if authorization else {}
        self.client = type("Client", (), {"host": "127.0.0.1"})()


@pytest.mark.anyio
async def test_cache_hit() -> None:
    redis = FakeRedis()
    await redis.set(
        ROOMS_CACHE_KEY,
        json.dumps([{"id": "cached", "name": "A101", "building": None, "floor": None, "capacity": None}]),
        ex=60,
    )
    repository = FakeRepository()
    service = CatalogService(repository, CacheService(redis, 60), EventBus(redis, "test"))

    rooms = await service.list_rooms()

    assert rooms[0].id == "cached"
    assert repository.list_calls == 0


@pytest.mark.anyio
async def test_cache_miss_writes_cache_with_ttl() -> None:
    redis = FakeRedis()
    repository = FakeRepository()
    service = CatalogService(repository, CacheService(redis, 30), EventBus(redis, "test"))

    rooms = await service.list_rooms()

    assert rooms[0].id == "room-1"
    assert repository.list_calls == 1
    assert ROOMS_CACHE_KEY in redis.values
    assert redis.expirations[ROOMS_CACHE_KEY] == 30


@pytest.mark.anyio
async def test_cache_invalidation_and_pubsub_on_create() -> None:
    redis = FakeRedis()
    cache = CacheService(redis, 60)
    await cache.set_json(ROOMS_CACHE_KEY, [{"id": "old"}])
    service = CatalogService(FakeRepository(), cache, EventBus(redis, "test"))

    created = await service.create_room(RoomCreate(name="A102"))

    assert created.name == "A102"
    assert ROOMS_CACHE_KEY in redis.deleted
    assert redis.published[0][0] == EventChannel.ROOMS.value


@pytest.mark.anyio
async def test_redis_unavailable_is_ignored() -> None:
    cache = CacheService(None, 60)

    await cache.set_json("key", {"value": 1})
    value = await cache.get_json("key")

    assert value is None


@pytest.mark.anyio
async def test_rate_limit_allows_then_blocks() -> None:
    redis = FakeRedis()
    limiter = RateLimiter(redis, enabled=True, requests=2, window_seconds=60)
    request = FakeRequest()

    first = await limiter.check(request)
    second = await limiter.check(request)
    third = await limiter.check(request)

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False


@pytest.mark.anyio
async def test_rate_limit_window_expiration_is_set() -> None:
    redis = FakeRedis()
    limiter = RateLimiter(redis, enabled=True, requests=10, window_seconds=45)

    result = await limiter.check(FakeRequest())

    assert result.allowed is True
    assert next(iter(redis.expirations.values())) == 45
