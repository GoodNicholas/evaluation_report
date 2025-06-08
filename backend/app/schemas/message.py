from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    """Base message schema."""

    body: str = Field(..., min_length=1, max_length=10000)


class MessageCreate(MessageBase):
    """Message creation schema."""

    pass


class MessageUpdate(BaseModel):
    """Message update schema."""

    read: bool


class MessageInDB(MessageBase):
    """Message database schema."""

    id: int
    dialog_id: int
    sender_id: int
    created_at: datetime
    read: bool

    class Config:
        from_attributes = True


class DialogBase(BaseModel):
    """Base dialog schema."""

    course_id: int
    teacher_id: int
    student_id: int


class DialogCreate(DialogBase):
    """Dialog creation schema."""

    pass


class DialogInDB(DialogBase):
    """Dialog database schema."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DialogWithMessages(DialogInDB):
    """Dialog schema with messages."""

    messages: list[MessageInDB] 