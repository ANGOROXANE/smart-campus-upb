from fastapi import APIRouter, Depends, HTTPException, status

from app.core.exceptions import DuplicateResourceError
from app.core.security import require_role
from app.models.sensor import Sensor, SensorCreate
from app.models.user import UserInDB, UserRole
from app.services.catalog import CatalogService, get_catalog_service


router = APIRouter(tags=["sensors"])


@router.get("/sensors", response_model=list[Sensor], summary="List sensors")
async def list_sensors(
    service: CatalogService = Depends(get_catalog_service),
) -> list[Sensor]:
    return await service.list_sensors()


@router.post(
    "/sensors",
    response_model=Sensor,
    status_code=status.HTTP_201_CREATED,
    summary="Create sensor",
)
async def create_sensor(
    sensor: SensorCreate,
    service: CatalogService = Depends(get_catalog_service),
    current_admin: UserInDB = Depends(require_role(UserRole.ADMIN)),
) -> Sensor:
    try:
        return await service.create_sensor(sensor)
    except DuplicateResourceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
