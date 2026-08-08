from fastapi import APIRouter, Depends, HTTPException, status

from app.core.exceptions import DuplicateResourceError
from app.core.security import require_role
from app.models.room import Room, RoomCreate
from app.models.user import UserInDB, UserRole
from app.services.catalog import CatalogService, get_catalog_service


router = APIRouter(tags=["rooms"])


@router.get("/rooms", response_model=list[Room], summary="List rooms")
async def list_rooms(
    service: CatalogService = Depends(get_catalog_service),
) -> list[Room]:
    return await service.list_rooms()


@router.post(
    "/rooms",
    response_model=Room,
    status_code=status.HTTP_201_CREATED,
    summary="Create room",
)
async def create_room(
    room: RoomCreate,
    service: CatalogService = Depends(get_catalog_service),
    current_admin: UserInDB = Depends(require_role(UserRole.ADMIN)),
) -> Room:
    try:
        return await service.create_room(room)
    except DuplicateResourceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
