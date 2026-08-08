from datetime import datetime, timezone
from typing import Any

import pytest

from app.models.measurement import MeasurementCreate
from app.services.measurements import InfluxMeasurementService


class FakeWriteApi:
    def __init__(self) -> None:
        self.records: list[Any] = []

    def write(self, bucket: str, org: str, record: Any) -> None:
        self.records.append({"bucket": bucket, "org": org, "record": record})


class FakeRecord:
    def __init__(self, values: dict[str, Any]) -> None:
        self.values = values


class FakeTable:
    def __init__(self, records: list[FakeRecord]) -> None:
        self.records = records


class FakeQueryApi:
    def __init__(self, timestamp: datetime) -> None:
        self.timestamp = timestamp
        self.queries: list[str] = []

    def query(self, query: str, org: str) -> list[FakeTable]:
        self.queries.append(query)
        return [
            FakeTable(
                [
                    FakeRecord(
                        {
                            "_time": self.timestamp,
                            "room": "A101",
                            "sensor": "temp-1",
                            "_field": "temperature",
                            "_value": 25.5,
                        }
                    ),
                    FakeRecord(
                        {
                            "_time": self.timestamp,
                            "room": "A101",
                            "sensor": "temp-1",
                            "_field": "presence",
                            "_value": True,
                        }
                    ),
                ]
            )
        ]


class FakeInfluxClient:
    def __init__(self) -> None:
        self.write_api_instance = FakeWriteApi()
        self.query_api_instance = FakeQueryApi(
            datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
        )

    def write_api(self, write_options: Any) -> FakeWriteApi:
        return self.write_api_instance

    def query_api(self) -> FakeQueryApi:
        return self.query_api_instance

    def ping(self) -> bool:
        return True


@pytest.mark.anyio
async def test_write_measurement() -> None:
    client = FakeInfluxClient()
    service = InfluxMeasurementService(client=client, org="upb", bucket="campus")
    measurement = MeasurementCreate(
        room="A101",
        sensor="temp-1",
        temperature=25.5,
        presence=True,
        timestamp=datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc),
    )

    created = await service.write_measurement(measurement)

    assert created.room == "A101"
    assert created.temperature == 25.5
    assert len(client.write_api_instance.records) == 1


@pytest.mark.anyio
async def test_read_latest_measurements() -> None:
    client = FakeInfluxClient()
    service = InfluxMeasurementService(client=client, org="upb", bucket="campus")

    measurements = await service.get_latest_measurements(limit=5)

    assert len(measurements) == 1
    assert measurements[0].room == "A101"
    assert measurements[0].presence is True


@pytest.mark.anyio
async def test_read_measurement_history() -> None:
    client = FakeInfluxClient()
    service = InfluxMeasurementService(client=client, org="upb", bucket="campus")

    measurements = await service.get_history(room="A101", sensor="temp-1")

    assert len(measurements) == 1
    assert measurements[0].sensor == "temp-1"
