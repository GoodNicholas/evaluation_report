from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_register_first_user(
    async_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test registering first user (admin)."""
    user_in = UserCreate(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="password123",
    )
    response = await async_client.post("/auth/register", json=user_in.dict())
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_in.email
    assert data["first_name"] == user_in.first_name
    assert data["last_name"] == user_in.last_name
    assert "id" in data
    assert "password" not in data

    # Verify user was created with admin role
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()
    assert user is not None
    assert any(r.name == "admin" for r in user.roles)


@pytest.mark.asyncio
async def test_register_second_user(
    async_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test registering second user (should fail)."""
    # Create admin role and user
    admin_role = Role(name="admin")
    db.add(admin_role)
    admin = User(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password_hash=get_password_hash("password123"),
    )
    admin.roles.append(admin_role)
    db.add(admin)
    await db.commit()

    # Try to register another user
    user_in = UserCreate(
        email="user@example.com",
        first_name="Regular",
        last_name="User",
        password="password123",
    )
    response = await async_client.post("/auth/register", json=user_in.dict())
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_login(
    async_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test login."""
    # Create user
    user = User(
        email="user@example.com",
        first_name="Test",
        last_name="User",
        password_hash=get_password_hash("password123"),
    )
    db.add(user)
    await db.commit()

    # Login
    response = await async_client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(
    async_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test login with wrong password."""
    # Create user
    user = User(
        email="user@example.com",
        first_name="Test",
        last_name="User",
        password_hash=get_password_hash("password123"),
    )
    db.add(user)
    await db.commit()

    # Try to login with wrong password
    response = await async_client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(
    async_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test refresh token."""
    # Create user and login
    user = User(
        email="user@example.com",
        first_name="Test",
        last_name="User",
        password_hash=get_password_hash("password123"),
    )
    db.add(user)
    await db.commit()

    login_response = await async_client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": "password123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    # Refresh token
    response = await async_client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_me(
    async_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test /me endpoint."""
    # Create user and login
    user = User(
        email="user@example.com",
        first_name="Test",
        last_name="User",
        password_hash=get_password_hash("password123"),
    )
    db.add(user)
    await db.commit()

    login_response = await async_client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Get user info
    response = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email
    assert data["first_name"] == user.first_name
    assert data["last_name"] == user.last_name 