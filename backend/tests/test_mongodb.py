from typing import Any

import pytest

from app.models.room import RoomCreate
from app.models.sensor import SensorCreate
from app.repositories.mongo import MongoRepository


class InsertOneResult:
    def __init__(self, inserted_id: str) -> None:
        self.inserted_id = inserted_id


class FakeCursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._documents = documents

    async def to_list(self, length: int) -> list[dict[str, Any]]:
        return self._documents[:length]


class FakeCollection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    async def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        inserted_id = str(len(self.documents) + 1)
        self.documents.append({"_id": inserted_id, **document})
        return InsertOneResult(inserted_id)

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        return next(
            (item for item in self.documents if item["_id"] == query["_id"]),
            None,
        )

    def find(self) -> FakeCursor:
        return FakeCursor(self.documents)


class FakeDatabase:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}

    def __getitem__(self, collection_name: str) -> FakeCollection:
        return self.collections.setdefault(collection_name, FakeCollection())


@pytest.mark.anyio
async def test_create_and_list_room() -> None:
    repository = MongoRepository(FakeDatabase())

    created = await repository.create_room(
        RoomCreate(name="A101", building="A", floor=1, capacity=40)
    )
    rooms = await repository.list_rooms()

    assert created.id == "1"
    assert created.name == "A101"
    assert len(rooms) == 1
    assert rooms[0].building == "A"


@pytest.mark.anyio
async def test_create_and_list_sensor() -> None:
    repository = MongoRepository(FakeDatabase())

    created = await repository.create_sensor(
        SensorCreate(
            name="Temperature A101",
            sensor_type="temperature",
            room="A101",
            unit="celsius",
        )
    )
    sensors = await repository.list_sensors()

    assert created.id == "1"
    assert created.sensor_type == "temperature"
    assert len(sensors) == 1
    assert sensors[0].room == "A101"
