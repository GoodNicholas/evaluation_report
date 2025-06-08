from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TokenPurpose(str, Enum):
    """Token purpose enum."""

    BIND = "bind"


class TelegramToken(Base):
    """Telegram token model."""

    __tablename__ = "telegram_tokens"

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    purpose: Mapped[TokenPurpose] = mapped_column(
        SQLEnum(TokenPurpose),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="telegram_tokens")

    def __repr__(self) -> str:
        return f"<TelegramToken {self.token[:8]}...>" 