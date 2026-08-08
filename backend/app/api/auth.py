from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.core.exceptions import DuplicateResourceError
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models.user import Token, UserCreate, UserInDB, UserLogin, UserPublic, UserRole
from app.repositories.mongo import MongoRepository, get_mongo_repository


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
)
async def register(
    user: UserCreate,
    repository: MongoRepository = Depends(get_mongo_repository),
) -> UserPublic:
    try:
        return await repository.create_user(
            email=user.email,
            password_hash=hash_password(user.password),
            role=UserRole.USER,
        )
    except DuplicateResourceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post("/login", response_model=Token, summary="Login and get an access token")
async def login(
    credentials: UserLogin,
    repository: MongoRepository = Depends(get_mongo_repository),
    settings: Settings = Depends(get_settings),
) -> Token:
    user = await repository.get_user_by_email(credentials.email)
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token, expires_at = create_access_token(subject=user.id, settings=settings)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return Token(access_token=token, expires_at=expires_at, user=UserPublic(**user.model_dump()))


@router.get("/me", response_model=UserPublic, summary="Get current user")
async def me(current_user: UserInDB = Depends(get_current_user)) -> UserPublic:
    return UserPublic(**current_user.model_dump())
