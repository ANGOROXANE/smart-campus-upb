from datetime import datetime, timezone

from pydantic import AliasChoices, BaseModel, Field, model_validator


class MeasurementCreate(BaseModel):
    room: str = Field(min_length=1, validation_alias=AliasChoices("room", "salle"))
    sensor: str = Field(default="manual", min_length=1)
    temperature: float | None = Field(default=None, ge=-50, le=80)
    presence: bool | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def require_a_value(self) -> "MeasurementCreate":
        if self.temperature is None and self.presence is None:
            raise ValueError("temperature or presence is required")
        return self


class Measurement(MeasurementCreate):
    pass
