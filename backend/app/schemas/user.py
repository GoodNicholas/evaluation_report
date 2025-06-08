from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr


class RoleBase(BaseModel):
    """Base role schema."""

    name: str


class RoleCreate(RoleBase):
    """Role creation schema."""

    pass


class Role(RoleBase):
    """Role schema."""

    id: int

    class Config:
        """Pydantic config."""

        from_attributes = True


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    first_name: str
    last_name: str


class UserCreate(UserBase):
    """User creation schema."""

    password: str


class UserUpdate(UserBase):
    """User update schema."""

    password: str | None = None


class User(UserBase):
    """User schema."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    roles: List[Role]

    class Config:
        """Pydantic config."""

        from_attributes = True


class Token(BaseModel):
    """Token schema."""

    access_token: str
    refresh_token: str


class TokenPayload(BaseModel):
    """Token payload schema."""

    sub: str | None = None 