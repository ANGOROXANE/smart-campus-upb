from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    name: str = Field(min_length=1)
    building: str | None = None
    floor: int | None = None
    capacity: int | None = Field(default=None, ge=0)


class Room(RoomCreate):
    id: str
