from typing import Any

from bson import ObjectId
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.db.dependencies import get_mongo_database
from app.core.exceptions import DuplicateResourceError
from app.db.mongodb import COLLECTION_ROOMS, COLLECTION_SENSORS, COLLECTION_USERS
from app.models.room import Room, RoomCreate
from app.models.sensor import Sensor, SensorCreate
from app.models.user import UserInDB, UserPublic, UserRole


def _document_to_model_data(document: dict[str, Any]) -> dict[str, Any]:
    data = dict(document)
    data["id"] = str(data.pop("_id"))
    return data


def _object_id(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except Exception:
        return None


class MongoRepository:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._database = database

    async def create_room(self, room: RoomCreate) -> Room:
        collection = self._database[COLLECTION_ROOMS]
        try:
            result = await collection.insert_one(room.model_dump())
        except DuplicateKeyError as exc:
            raise DuplicateResourceError("room") from exc
        document = await collection.find_one({"_id": result.inserted_id})
        return Room.model_validate(_document_to_model_data(document))

    async def list_rooms(self) -> list[Room]:
        collection = self._database[COLLECTION_ROOMS]
        documents = await collection.find().to_list(length=100)
        return [Room.model_validate(_document_to_model_data(item)) for item in documents]

    async def create_sensor(self, sensor: SensorCreate) -> Sensor:
        collection = self._database[COLLECTION_SENSORS]
        try:
            result = await collection.insert_one(sensor.model_dump())
        except DuplicateKeyError as exc:
            raise DuplicateResourceError("sensor") from exc
        document = await collection.find_one({"_id": result.inserted_id})
        return Sensor.model_validate(_document_to_model_data(document))

    async def list_sensors(self) -> list[Sensor]:
        collection = self._database[COLLECTION_SENSORS]
        documents = await collection.find().to_list(length=100)
        return [Sensor.model_validate(_document_to_model_data(item)) for item in documents]

    async def create_user(
        self,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.USER,
    ) -> UserPublic:
        collection = self._database[COLLECTION_USERS]
        document = {
            "email": email.lower(),
            "password_hash": password_hash,
            "role": role.value,
            "is_active": True,
        }
        try:
            result = await collection.insert_one(document)
        except DuplicateKeyError as exc:
            raise DuplicateResourceError("user") from exc
        created = await collection.find_one({"_id": result.inserted_id})
        return UserPublic.model_validate(_document_to_model_data(created))

    async def get_user_by_email(self, email: str) -> UserInDB | None:
        document = await self._database[COLLECTION_USERS].find_one({"email": email.lower()})
        if document is None:
            return None
        return UserInDB.model_validate(_document_to_model_data(document))

    async def get_user_by_id(self, user_id: str) -> UserInDB | None:
        object_id = _object_id(user_id)
        if object_id is None:
            return None
        document = await self._database[COLLECTION_USERS].find_one({"_id": object_id})
        if document is None:
            return None
        return UserInDB.model_validate(_document_to_model_data(document))


def get_mongo_repository(
    database: AsyncIOMotorDatabase = Depends(get_mongo_database),
) -> MongoRepository:
    return MongoRepository(database)
