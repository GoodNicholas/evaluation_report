from datetime import datetime

from pydantic import BaseModel


class TelegramBindToken(BaseModel):
    """Telegram bind token schema."""

    user_id: int
    expires_at: datetime 