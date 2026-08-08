from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.dependencies import get_mongo_database
from app.db.mongodb import ping_mongodb
from app.db.redis import ping_redis
from app.services.measurements import (
    InfluxMeasurementService,
    get_measurement_service,
)
from app.services.metrics import set_dependency_status
from fastapi import Request


router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    mongodb: Literal["up", "down"]
    influxdb: Literal["up", "down"]
    redis: Literal["up", "down"]


@router.get("/health", response_model=HealthResponse, summary="Application health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/health/live", response_model=HealthResponse, summary="Liveness probe")
def live() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=ReadinessResponse, summary="Readiness probe")
async def ready(
    request: Request,
    mongo_database=Depends(get_mongo_database),
    measurement_service: InfluxMeasurementService = Depends(get_measurement_service),
) -> ReadinessResponse:
    mongodb_status: Literal["up", "down"] = (
        "up" if await ping_mongodb(mongo_database) else "down"
    )
    influxdb_status: Literal["up", "down"] = (
        "up" if await measurement_service.ping() else "down"
    )
    redis_status: Literal["up", "down"] = (
        "up" if await ping_redis(getattr(request.app.state, "redis", None)) else "down"
    )
    set_dependency_status("mongodb", mongodb_status == "up")
    set_dependency_status("influxdb", influxdb_status == "up")
    set_dependency_status("redis", redis_status == "up")
    return ReadinessResponse(
        mongodb=mongodb_status,
        influxdb=influxdb_status,
        redis=redis_status,
    )
