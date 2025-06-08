from __future__ import annotations

from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Role(Base):
    """Role model."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>" 