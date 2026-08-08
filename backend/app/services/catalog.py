from fastapi import Request

from app.core.exceptions import DuplicateResourceError
from app.models.room import Room, RoomCreate
from app.models.sensor import Sensor, SensorCreate
from app.repositories.mongo import MongoRepository
from app.services.cache import CacheService
from app.services.events import EventBus, EventChannel


ROOMS_CACHE_KEY = "rooms:list:v1"
SENSORS_CACHE_KEY = "sensors:list:v1"


class CatalogService:
    def __init__(
        self,
        repository: MongoRepository,
        cache: CacheService,
        event_bus: EventBus,
    ) -> None:
        self._repository = repository
        self._cache = cache
        self._event_bus = event_bus

    async def list_rooms(self) -> list[Room]:
        cached = await self._cache.get_json(ROOMS_CACHE_KEY)
        if isinstance(cached, list):
            return [Room.model_validate(item) for item in cached]

        rooms = await self._repository.list_rooms()
        await self._cache.set_json(
            ROOMS_CACHE_KEY,
            [room.model_dump(mode="json") for room in rooms],
        )
        return rooms

    async def create_room(self, room: RoomCreate) -> Room:
        try:
            created = await self._repository.create_room(room)
        except DuplicateResourceError:
            raise
        await self._cache.delete(ROOMS_CACHE_KEY)
        await self._event_bus.publish(
            EventChannel.ROOMS,
            "room.created",
            payload=created.model_dump(mode="json"),
            cache_keys=[ROOMS_CACHE_KEY],
        )
        return created

    async def list_sensors(self) -> list[Sensor]:
        cached = await self._cache.get_json(SENSORS_CACHE_KEY)
        if isinstance(cached, list):
            return [Sensor.model_validate(item) for item in cached]

        sensors = await self._repository.list_sensors()
        await self._cache.set_json(
            SENSORS_CACHE_KEY,
            [sensor.model_dump(mode="json") for sensor in sensors],
        )
        return sensors

    async def create_sensor(self, sensor: SensorCreate) -> Sensor:
        try:
            created = await self._repository.create_sensor(sensor)
        except DuplicateResourceError:
            raise
        await self._cache.delete(SENSORS_CACHE_KEY)
        await self._event_bus.publish(
            EventChannel.SENSORS,
            "sensor.created",
            payload=created.model_dump(mode="json"),
            cache_keys=[SENSORS_CACHE_KEY],
        )
        return created


def get_catalog_service(request: Request) -> CatalogService:
    return request.app.state.catalog_service
