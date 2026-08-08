from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Event(BaseModel):
    id: str | None = None
    event_type: str
    message: str
    room: str | None = None
    sensor: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
