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
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """Login user and return access token."""
    # Get user
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "roles": [r.name for r in user.roles]}
    )

    # Create refresh token
    refresh_token = RefreshToken(
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    db.add(refresh_token)
    await db.commit()
    await db.refresh(refresh_token)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token.token,
        token_type="bearer",
    )


@router.post("/logout")
async def logout(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Logout user and revoke refresh token."""
    # Revoke all refresh tokens for the user
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == current_user.id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    tokens = result.scalars().all()
    for token in tokens:
        token.revoked_at = datetime.utcnow()
    await db.commit()

    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Token:
    """Refresh access token."""
    # Create new access token
    access_token = create_access_token(
        data={"sub": current_user.email, "roles": [r.name for r in current_user.roles]}
    )

    # Create new refresh token
    refresh_token = RefreshToken(
        user_id=current_user.id,
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    db.add(refresh_token)
    await db.commit()
    await db.refresh(refresh_token)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token.token,
        token_type="bearer",
    )


@router.get("/me", response_model=UserSchema)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current user."""
    return current_user 