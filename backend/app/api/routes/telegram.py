from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.telegram import TelegramBindToken

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