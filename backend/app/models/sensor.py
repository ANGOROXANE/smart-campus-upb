from pydantic import BaseModel, Field


class SensorCreate(BaseModel):
    name: str = Field(min_length=1)
    sensor_type: str = Field(min_length=1)
    room: str = Field(min_length=1)
    unit: str | None = None


class Sensor(SensorCreate):
    id: str
