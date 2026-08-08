from fastapi import APIRouter, Depends, Query, status

from app.models.measurement import Measurement, MeasurementCreate
from app.services.measurements import (
    InfluxMeasurementService,
    get_measurement_service,
)


router = APIRouter(tags=["measurements"])


@router.post(
    "/measurements",
    response_model=Measurement,
    status_code=status.HTTP_201_CREATED,
    summary="Write campus measurement",
)
async def create_measurement(
    measurement: MeasurementCreate,
    service: InfluxMeasurementService = Depends(get_measurement_service),
) -> Measurement:
    return await service.write_measurement(measurement)


@router.get(
    "/measurements/latest",
    response_model=list[Measurement],
    summary="Read latest campus measurements",
)
async def latest_measurements(
    limit: int = Query(default=10, ge=1, le=100),
    service: InfluxMeasurementService = Depends(get_measurement_service),
) -> list[Measurement]:
    return await service.get_latest_measurements(limit=limit)


@router.get(
    "/measurements/history",
    response_model=list[Measurement],
    summary="Read campus measurement history",
)
async def measurement_history(
    start: str = Query(default="-24h"),
    room: str | None = None,
    sensor: str | None = None,
    service: InfluxMeasurementService = Depends(get_measurement_service),
) -> list[Measurement]:
    return await service.get_history(start=start, room=room, sensor=sensor)
