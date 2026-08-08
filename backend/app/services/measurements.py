import asyncio
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from fastapi import Request
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from app.models.measurement import Measurement, MeasurementCreate
from app.services.cache import CacheService
from app.services.events import EventBus, EventChannel


MEASUREMENT_NAME = "campus_measurements"
LATEST_MEASUREMENTS_CACHE_PREFIX = "measurements:latest"


def _escape_flux_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


class InfluxMeasurementService:
    def __init__(
        self,
        client: InfluxDBClient,
        org: str,
        bucket: str,
        cache: CacheService | None = None,
        event_bus: EventBus | None = None,
        latest_cache_ttl_seconds: int = 10,
    ) -> None:
        self._client = client
        self._org = org
        self._bucket = bucket
        self._cache = cache
        self._event_bus = event_bus
        self._latest_cache_ttl_seconds = latest_cache_ttl_seconds
        self._write_api = client.write_api(write_options=SYNCHRONOUS)
        self._query_api = client.query_api()

    async def ping(self) -> bool:
        try:
            return bool(await asyncio.to_thread(self._client.ping))
        except Exception:
            return False

    async def write_measurement(self, measurement: MeasurementCreate) -> Measurement:
        await asyncio.to_thread(self._write_measurement_sync, measurement)
        created = Measurement.model_validate(measurement.model_dump())
        if self._cache is not None:
            await self._cache.delete_pattern(f"{LATEST_MEASUREMENTS_CACHE_PREFIX}:*")
        if self._event_bus is not None:
            await self._event_bus.publish(
                EventChannel.MEASUREMENTS,
                "measurement.created",
                payload=created.model_dump(mode="json"),
                cache_patterns=[f"{LATEST_MEASUREMENTS_CACHE_PREFIX}:*"],
            )
        return created

    async def get_latest_measurements(self, limit: int = 10) -> list[Measurement]:
        cache_key = f"{LATEST_MEASUREMENTS_CACHE_PREFIX}:{limit}:v1"
        if self._cache is not None:
            cached = await self._cache.get_json(cache_key)
            if isinstance(cached, list):
                return [Measurement.model_validate(item) for item in cached]

        query = f'''
from(bucket: "{_escape_flux_string(self._bucket)}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT_NAME}")
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {limit})
'''
        tables = await asyncio.to_thread(
            self._query_api.query,
            query=query,
            org=self._org,
        )
        measurements = _flux_tables_to_measurements(tables)
        if self._cache is not None:
            await self._cache.set_json(
                cache_key,
                [measurement.model_dump(mode="json") for measurement in measurements],
                ttl_seconds=self._latest_cache_ttl_seconds,
            )
        return measurements

    async def get_history(
        self,
        start: str = "-24h",
        room: str | None = None,
        sensor: str | None = None,
    ) -> list[Measurement]:
        filters = [f'r._measurement == "{MEASUREMENT_NAME}"']
        if room:
            filters.append(f'r.room == "{_escape_flux_string(room)}"')
        if sensor:
            filters.append(f'r.sensor == "{_escape_flux_string(sensor)}"')

        filter_expression = " and ".join(filters)
        query = f'''
from(bucket: "{_escape_flux_string(self._bucket)}")
  |> range(start: {start})
  |> filter(fn: (r) => {filter_expression})
  |> sort(columns: ["_time"], desc: false)
'''
        tables = await asyncio.to_thread(
            self._query_api.query,
            query=query,
            org=self._org,
        )
        return _flux_tables_to_measurements(tables)

    def _write_measurement_sync(self, measurement: MeasurementCreate) -> None:
        point = (
            Point(MEASUREMENT_NAME)
            .tag("room", measurement.room)
            .tag("sensor", measurement.sensor)
            .time(measurement.timestamp)
        )
        if measurement.temperature is not None:
            point = point.field("temperature", measurement.temperature)
        if measurement.presence is not None:
            point = point.field("presence", measurement.presence)

        self._write_api.write(
            bucket=self._bucket,
            org=self._org,
            record=point,
        )


def _flux_tables_to_measurements(tables: Iterable[Any]) -> list[Measurement]:
    grouped: dict[tuple[datetime, str, str], dict[str, Any]] = {}
    for table in tables:
        for record in table.records:
            values = record.values
            timestamp = values.get("_time")
            room = values.get("room")
            sensor = values.get("sensor")
            field = values.get("_field")
            if not timestamp or not room or not sensor or not field:
                continue

            key = (timestamp, room, sensor)
            item = grouped.setdefault(
                key,
                {
                    "timestamp": timestamp,
                    "room": room,
                    "sensor": sensor,
                    "temperature": None,
                    "presence": None,
                },
            )
            if field == "temperature":
                item["temperature"] = values.get("_value")
            if field == "presence":
                item["presence"] = values.get("_value")

    return [Measurement.model_validate(item) for item in grouped.values()]


def get_measurement_service(request: Request) -> InfluxMeasurementService:
    return request.app.state.measurement_service
