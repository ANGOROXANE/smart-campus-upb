from enum import Enum

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class UserBase(BaseModel):
    email: str = Field(min_length=3)
    role: UserRole = UserRole.USER
    is_active: bool = True


class UserCreate(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class UserPublic(UserBase):
    id: str


class UserInDB(UserPublic):
    password_hash: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: int
    user: UserPublic


User = UserPublic
