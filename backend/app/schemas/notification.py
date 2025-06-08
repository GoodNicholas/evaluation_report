from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.notification import NotificationType


class NotificationBase(BaseModel):
    """Base notification schema."""

    type: NotificationType
    payload: dict = Field(..., description="Notification payload")


class NotificationCreate(NotificationBase):
    """Notification creation schema."""

    user_id: int


class NotificationUpdate(BaseModel):
    """Notification update schema."""

    delivered: bool


class NotificationInDB(NotificationBase):
    """Notification database schema."""

    id: int
    user_id: int
    delivered: bool
    created_at: datetime

    class Config:
        from_attributes = True 