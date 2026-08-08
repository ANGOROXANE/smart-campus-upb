from typing import Final

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING

from app.core.config import Settings


COLLECTION_USERS: Final[str] = "users"
COLLECTION_ROOMS: Final[str] = "rooms"
COLLECTION_SENSORS: Final[str] = "sensors"
COLLECTION_EVENTS: Final[str] = "events"
COLLECTIONS: Final[tuple[str, ...]] = (
    COLLECTION_USERS,
    COLLECTION_ROOMS,
    COLLECTION_SENSORS,
    COLLECTION_EVENTS,
)


def create_mongo_client(settings: Settings) -> AsyncIOMotorClient:
    return AsyncIOMotorClient(
        settings.mongo_uri.get_secret_value(),
        serverSelectionTimeoutMS=2000,
        uuidRepresentation="standard",
    )


def get_mongo_database_from_client(
    client: AsyncIOMotorClient,
    settings: Settings,
) -> AsyncIOMotorDatabase:
    return client[settings.mongo_database]


async def ping_mongodb(database: AsyncIOMotorDatabase) -> bool:
    try:
        await database.command("ping")
    except Exception:
        return False
    return True


async def ensure_mongo_indexes(database: AsyncIOMotorDatabase) -> None:
    await database[COLLECTION_USERS].create_index(
        [("email", ASCENDING)],
        unique=True,
        name="users_email_unique",
    )
    await database[COLLECTION_ROOMS].create_index(
        [("name", ASCENDING)],
        unique=True,
        name="rooms_name_unique",
    )
    await database[COLLECTION_SENSORS].create_index(
        [("room", ASCENDING), ("name", ASCENDING)],
        unique=True,
        name="sensors_room_name_unique",
    )
    await database[COLLECTION_EVENTS].create_index(
        [("created_at", ASCENDING)],
        name="events_created_at",
    )
