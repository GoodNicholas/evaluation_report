from datetime import datetime, timedelta
from typing import Annotated

from sqlalchemy import select

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.telegram import TelegramBindToken, TelegramBindRequest

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/bind-token")
async def generate_bind_token(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Generate a token for binding Telegram account."""
    # Generate token
    token = f"bind_{current_user.id}_{datetime.utcnow().timestamp()}"

    # Create token data
    token_data = TelegramBindToken(
        user_id=current_user.id,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )

    # Store token in Redis
    redis = await get_redis()
    await redis.set(
        f"telegram:bind_token:{token}",
        token_data.json(),
        ex=900,  # 15 minutes
    )

    return {"token": token}


@router.post("/bind")
async def bind_account(
    payload: TelegramBindRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Bind Telegram account using a token."""
    redis = await get_redis()
    token_key = f"telegram:bind_token:{payload.token}"
    token_data_raw = await redis.get(token_key)
    if not token_data_raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    try:
        token_data = TelegramBindToken.parse_raw(token_data_raw)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    if datetime.utcnow() > token_data.expires_at:
        await redis.delete(token_key)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token has expired")

    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    setattr(user, "telegram_id", payload.telegram_id)
    await db.commit()
    await redis.delete(token_key)
    return {"message": "Telegram account bound"}
