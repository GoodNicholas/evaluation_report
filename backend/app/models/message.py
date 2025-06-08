from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Dialog(Base):
    """Dialog model for chat between teacher and student."""

    __tablename__ = "dialogs"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="dialogs")
    teacher: Mapped["User"] = relationship(
        "User", foreign_keys=[teacher_id], back_populates="teacher_dialogs"
    )
    student: Mapped["User"] = relationship(
        "User", foreign_keys=[student_id], back_populates="student_dialogs"
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="dialog", cascade="all, delete-orphan"
    )


class Message(Base):
    """Message model for chat messages."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    dialog_id: Mapped[int] = mapped_column(ForeignKey("dialogs.id", ondelete="CASCADE"))
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    read: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    dialog: Mapped["Dialog"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(back_populates="messages") 