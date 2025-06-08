from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List

from sqlalchemy import Enum as SQLEnum, ForeignKey, String, Column, Integer, DateTime, Boolean
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

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="owned_courses")
    materials: Mapped[List["Material"]] = relationship(
        "Material",
        back_populates="course",
    )
    enrolments: Mapped[List["Enrolment"]] = relationship(
        "Enrolment",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    roles: Mapped[List["CourseRole"]] = relationship(
        "CourseRole",
        back_populates="course",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Course {self.code}>" 