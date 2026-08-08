import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings
from app.models.measurement import Measurement, MeasurementCreate
from app.services.measurements import InfluxMeasurementService, get_measurement_service


router = APIRouter(prefix="/ingestion", tags=["ingestion"])


def require_node_red_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    if settings.node_red_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Node-RED ingestion key is not configured",
        )
    expected = settings.node_red_api_key.get_secret_value()
    if x_api_key is None or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ingestion API key",
        )


@router.post(
    "/measurements",
    response_model=Measurement,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a validated MQTT/Node-RED measurement",
)
async def ingest_measurement(
    measurement: MeasurementCreate,
    _: None = Depends(require_node_red_api_key),
    service: InfluxMeasurementService = Depends(get_measurement_service),
) -> Measurement:
    return await service.write_measurement(
        MeasurementCreate(
            room=measurement.room,
            sensor=measurement.sensor if measurement.sensor != "manual" else "node-red",
            temperature=measurement.temperature,
            presence=measurement.presence,
            timestamp=measurement.timestamp,
        )
    )
