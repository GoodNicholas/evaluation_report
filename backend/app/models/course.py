from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List

from sqlalchemy import Enum as SQLEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EnrolmentStatus(str, Enum):
    """Enrolment status enum."""

    INVITED = "invited"
    ACTIVE = "active"
    DROPPED = "dropped"


class Course(Base):
    """Course model."""

    __tablename__ = "courses"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="owned_courses")
    materials: Mapped[List["Material"]] = relationship(
        "Material",
        back_populates="course",
    )
    enrolments: Mapped[List["Enrolment"]] = relationship(
        "Enrolment",
        back_populates="course",
    )

    def __repr__(self) -> str:
        return f"<Course {self.code}>" 