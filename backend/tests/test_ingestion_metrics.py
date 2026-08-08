from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.models.measurement import Measurement, MeasurementCreate
from app.services.measurements import get_measurement_service


class FakeMeasurementService:
    def __init__(self) -> None:
        self.measurements: list[Measurement] = []

    async def write_measurement(self, measurement: MeasurementCreate) -> Measurement:
        created = Measurement.model_validate(measurement.model_dump())
        self.measurements.append(created)
        return created


@pytest.fixture
def ingestion_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, FakeMeasurementService]]:
    monkeypatch.setenv("NODE_RED_API_KEY", "node-red-test-key")
    get_settings.cache_clear()
    service = FakeMeasurementService()
    app.dependency_overrides[get_measurement_service] = lambda: service
    with TestClient(app) as client:
        yield client, service
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_ingest_node_red_measurement(
    ingestion_client: tuple[TestClient, FakeMeasurementService],
) -> None:
    client, service = ingestion_client
    timestamp = datetime(2026, 8, 8, 10, 0, tzinfo=timezone.utc).isoformat()

    response = client.post(
        "/ingestion/measurements",
        headers={"X-API-Key": "node-red-test-key"},
        json={
            "salle": "A101",
            "temperature": 24.2,
            "presence": True,
            "timestamp": timestamp,
        },
    )

    assert response.status_code == 201
    assert response.json()["room"] == "A101"
    assert response.json()["sensor"] == "node-red"
    assert len(service.measurements) == 1


def test_ingest_rejects_invalid_api_key(
    ingestion_client: tuple[TestClient, FakeMeasurementService],
) -> None:
    client, _ = ingestion_client

    response = client.post(
        "/ingestion/measurements",
        headers={"X-API-Key": "wrong"},
        json={"salle": "A101", "temperature": 24.2, "presence": True},
    )

    assert response.status_code == 401


def test_ingest_rejects_missing_measurement_values(
    ingestion_client: tuple[TestClient, FakeMeasurementService],
) -> None:
    client, _ = ingestion_client

    response = client.post(
        "/ingestion/measurements",
        headers={"X-API-Key": "node-red-test-key"},
        json={"salle": "A101"},
    )

    assert response.status_code == 422


def test_metrics_endpoint(ingestion_client: tuple[TestClient, FakeMeasurementService]) -> None:
    client, _ = ingestion_client

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "smart_campus_http_requests_total" in response.text
