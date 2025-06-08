from datetime import datetime

from pydantic import BaseModel


class TelegramBindRequest(BaseModel):
    """Request body for binding Telegram account."""

    token: str
    telegram_id: int


class TelegramBindToken(BaseModel):
    """Telegram bind token schema."""

    user_id: int
    expires_at: datetime 