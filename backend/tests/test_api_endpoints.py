from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.measurement import Measurement, MeasurementCreate
from app.models.room import Room, RoomCreate
from app.models.sensor import Sensor, SensorCreate
from app.models.user import UserInDB, UserRole
from app.repositories.mongo import get_mongo_repository
from app.core.security import get_current_user
from app.services.catalog import get_catalog_service
from app.services.measurements import get_measurement_service


class FakeMongoRepository:
    def __init__(self) -> None:
        self.rooms: list[Room] = []
        self.sensors: list[Sensor] = []

    async def create_room(self, room: RoomCreate) -> Room:
        created = Room(id=f"room-{len(self.rooms) + 1}", **room.model_dump())
        self.rooms.append(created)
        return created

    async def list_rooms(self) -> list[Room]:
        return self.rooms

    async def create_sensor(self, sensor: SensorCreate) -> Sensor:
        created = Sensor(id=f"sensor-{len(self.sensors) + 1}", **sensor.model_dump())
        self.sensors.append(created)
        return created

    async def list_sensors(self) -> list[Sensor]:
        return self.sensors


class FakeMeasurementService:
    def __init__(self) -> None:
        self.measurements: list[Measurement] = []

    async def write_measurement(
        self,
        measurement: MeasurementCreate,
    ) -> Measurement:
        created = Measurement.model_validate(measurement.model_dump())
        self.measurements.append(created)
        return created

    async def get_latest_measurements(self, limit: int = 10) -> list[Measurement]:
        return self.measurements[-limit:]

    async def get_history(
        self,
        start: str = "-24h",
        room: str | None = None,
        sensor: str | None = None,
    ) -> list[Measurement]:
        return [
            item
            for item in self.measurements
            if (room is None or item.room == room)
            and (sensor is None or item.sensor == sensor)
        ]


@pytest.fixture
def api_client() -> Iterator[TestClient]:
    repository = FakeMongoRepository()
    service = FakeMeasurementService()
    admin = UserInDB(
        id="admin-1",
        email="admin@example.com",
        password_hash="unused",
        role=UserRole.ADMIN,
        is_active=True,
    )
    app.dependency_overrides[get_mongo_repository] = lambda: repository
    app.dependency_overrides[get_catalog_service] = lambda: repository
    app.dependency_overrides[get_measurement_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: admin
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_create_and_list_rooms(api_client: TestClient) -> None:
    create_response = api_client.post(
        "/rooms",
        json={"name": "A101", "building": "A", "floor": 1, "capacity": 40},
    )
    list_response = api_client.get("/rooms")

    assert create_response.status_code == 201
    assert create_response.json()["name"] == "A101"
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == "room-1"


def test_create_and_list_sensors(api_client: TestClient) -> None:
    create_response = api_client.post(
        "/sensors",
        json={
            "name": "Temperature A101",
            "sensor_type": "temperature",
            "room": "A101",
            "unit": "celsius",
        },
    )
    list_response = api_client.get("/sensors")

    assert create_response.status_code == 201
    assert create_response.json()["sensor_type"] == "temperature"
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == "sensor-1"


def test_write_and_read_measurements(api_client: TestClient) -> None:
    timestamp = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc).isoformat()
    create_response = api_client.post(
        "/measurements",
        json={
            "room": "A101",
            "sensor": "temp-1",
            "temperature": 25.5,
            "presence": True,
            "timestamp": timestamp,
        },
    )
    latest_response = api_client.get("/measurements/latest")
    history_response = api_client.get(
        "/measurements/history",
        params={"room": "A101", "sensor": "temp-1"},
    )

    assert create_response.status_code == 201
    assert latest_response.status_code == 200
    assert history_response.status_code == 200
    assert latest_response.json()[0]["temperature"] == 25.5
    assert history_response.json()[0]["presence"] is True
