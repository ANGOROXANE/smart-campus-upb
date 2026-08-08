from collections.abc import Iterator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import UserInDB, UserPublic, UserRole
from app.repositories.mongo import get_mongo_repository
from app.services.catalog import get_catalog_service


class FakeAuthRepository:
    def __init__(self) -> None:
        self.users: dict[str, UserInDB] = {}
        self.email_index: dict[str, str] = {}

    async def create_user(
        self,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.USER,
    ) -> UserPublic:
        normalized = email.lower()
        if normalized in self.email_index:
            from app.core.exceptions import DuplicateResourceError

            raise DuplicateResourceError("user")
        user_id = f"user-{len(self.users) + 1}"
        user = UserInDB(
            id=user_id,
            email=normalized,
            password_hash=password_hash,
            role=role,
            is_active=True,
        )
        self.users[user_id] = user
        self.email_index[normalized] = user_id
        return UserPublic(**user.model_dump())

    async def get_user_by_email(self, email: str) -> UserInDB | None:
        user_id = self.email_index.get(email.lower())
        if user_id is None:
            return None
        return self.users[user_id]

    async def get_user_by_id(self, user_id: str) -> UserInDB | None:
        return self.users.get(user_id)


@pytest.fixture
def auth_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, FakeAuthRepository]]:
    monkeypatch.setenv("JWT_SECRET", "test-secret-with-at-least-32-bytes")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    get_settings.cache_clear()
    repository = FakeAuthRepository()
    app.dependency_overrides[get_mongo_repository] = lambda: repository
    with TestClient(app) as client:
        yield client, repository
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_register(auth_client: tuple[TestClient, FakeAuthRepository]) -> None:
    client, _ = auth_client

    response = client.post(
        "/auth/register",
        json={"email": "User@Example.com", "password": "password-123"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"
    assert response.json()["role"] == "user"
    assert "password_hash" not in response.json()


def test_login_valid(auth_client: tuple[TestClient, FakeAuthRepository]) -> None:
    client, _ = auth_client
    client.post("/auth/register", json={"email": "user@example.com", "password": "password-123"})

    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "password-123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_bad_password(auth_client: tuple[TestClient, FakeAuthRepository]) -> None:
    client, _ = auth_client
    client.post("/auth/register", json={"email": "user@example.com", "password": "password-123"})

    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_invalid_token(auth_client: tuple[TestClient, FakeAuthRepository]) -> None:
    client, _ = auth_client

    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401


def test_expired_token(auth_client: tuple[TestClient, FakeAuthRepository]) -> None:
    client, repository = auth_client
    user = UserInDB(
        id="user-1",
        email="user@example.com",
        password_hash=hash_password("password-123"),
        role=UserRole.USER,
        is_active=True,
    )
    repository.users[user.id] = user
    repository.email_index[user.email] = user.id
    token, _ = create_access_token(
        subject=user.id,
        settings=get_settings(),
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"


def test_access_without_token(auth_client: tuple[TestClient, FakeAuthRepository]) -> None:
    client, _ = auth_client

    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_returns_user(auth_client: tuple[TestClient, FakeAuthRepository]) -> None:
    client, _ = auth_client
    client.post("/auth/register", json={"email": "user@example.com", "password": "password-123"})
    login = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "password-123"},
    ).json()

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_user_cannot_create_room(auth_client: tuple[TestClient, FakeAuthRepository]) -> None:
    client, _ = auth_client
    client.post("/auth/register", json={"email": "user@example.com", "password": "password-123"})
    login = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "password-123"},
    ).json()

    response = client.post(
        "/rooms",
        json={"name": "A101"},
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )

    assert response.status_code == 403


def test_admin_can_create_room(auth_client: tuple[TestClient, FakeAuthRepository]) -> None:
    client, repository = auth_client
    admin = UserInDB(
        id="admin-1",
        email="admin@example.com",
        password_hash=hash_password("password-123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    repository.users[admin.id] = admin
    repository.email_index[admin.email] = admin.id
    token, _ = create_access_token(subject=admin.id, settings=get_settings())

    class FakeCatalogService:
        async def create_room(self, room):
            from app.models.room import Room

            return Room(id="room-1", **room.model_dump())

    app.dependency_overrides[get_catalog_service] = lambda: FakeCatalogService()

    response = client.post(
        "/rooms",
        json={"name": "A101"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["id"] == "room-1"
