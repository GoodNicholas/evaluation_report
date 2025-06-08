from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User


@pytest.mark.asyncio
async def test_generate_and_bind(async_client: AsyncClient, db: AsyncSession) -> None:
    user = User(
        email="tg@example.com",
        first_name="TG",
        last_name="User",
        password_hash=get_password_hash("pass"),
    )
    db.add(user)
    await db.commit()

    login_resp = await async_client.post(
        "/auth/login",
        data={"username": "tg@example.com", "password": "pass"},
    )
    access = login_resp.json()["access_token"]

    token_resp = await async_client.post(
        "/telegram/bind-token",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["token"]

    bind_resp = await async_client.post(
        "/auth/telegram/bind",
        json={"token": token, "telegram_id": 123},
    )
    assert bind_resp.status_code == 200
    assert bind_resp.json()["message"] == "Telegram account bound"
