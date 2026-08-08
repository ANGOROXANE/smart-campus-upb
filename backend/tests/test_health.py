from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.db.dependencies import get_mongo_database
from app.main import app
from app.services.measurements import get_measurement_service


class FakeMongoDatabase:
    async def command(self, command_name: str) -> dict[str, int]:
        return {"ok": 1}


class FakeMeasurementService:
    async def ping(self) -> bool:
        return True


class FakeRedis:
    async def ping(self) -> bool:
        return True


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_mongo_database] = lambda: FakeMongoDatabase()
    app.dependency_overrides[get_measurement_service] = lambda: FakeMeasurementService()
    with TestClient(app) as test_client:
        app.state.redis = FakeRedis()
        yield test_client
    app.dependency_overrides.clear()


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_live(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_ready(client: TestClient) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"mongodb": "up", "influxdb": "up", "redis": "up"}
