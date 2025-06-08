from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.schemas.user import Token, User as UserSchema, UserCreate

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_in: UserCreate,
) -> User:
    """Register new user."""
    # Check if any admin exists
    result = await db.execute(select(Role).where(Role.name == "admin"))
    admin_role = result.scalar_one_or_none()
    if admin_role:
        result = await db.execute(
            select(User).join(User.roles).where(Role.name == "admin")
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration is closed",
            )

    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        password_hash=get_password_hash(user_in.password),
    )

    # Assign role
    if not admin_role:
        admin_role = Role(name="admin")
        db.add(admin_role)
    user.roles.append(admin_role)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    db: Annotated[AsyncSession, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """Login user."""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    # Create refresh token
    refresh_token = RefreshToken(
        user_id=user.id,
        token=create_refresh_token(user.id),
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(refresh_token)
    await db.commit()

    return Token(
        access_token=create_access_token(user.id),
        refresh_token=refresh_token.token,
    )


@router.post("/refresh", response_model=Token)
async def refresh(
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: str,
) -> Token:
    """Refresh access token."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.revoked == False,  # noqa: E712
            RefreshToken.expires_at > datetime.utcnow(),
        )
    )
    token = result.scalar_one_or_none()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Create new refresh token
    new_refresh_token = RefreshToken(
        user_id=token.user_id,
        token=create_refresh_token(token.user_id),
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(new_refresh_token)

    # Revoke old token
    token.revoked = True
    await db.commit()

    return Token(
        access_token=create_access_token(token.user_id),
        refresh_token=new_refresh_token.token,
    )


@router.get("/me", response_model=UserSchema)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current user."""
    return current_user 