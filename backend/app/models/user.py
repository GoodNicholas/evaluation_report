from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
    )
    telegram_tokens: Mapped[List["TelegramToken"]] = relationship(
        "TelegramToken",
        back_populates="user",
    )
    owned_courses: Mapped[List["Course"]] = relationship(
        "Course",
        back_populates="owner",
    )
    enrolments: Mapped[List["Enrolment"]] = relationship(
        "Enrolment",
        back_populates="user",
    )
    uploaded_materials: Mapped[List["Material"]] = relationship(
        "Material",
        back_populates="uploader",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>" 