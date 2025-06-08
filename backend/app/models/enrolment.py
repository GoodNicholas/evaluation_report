from __future__ import annotations

from sqlalchemy import Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.course import EnrolmentStatus


class Enrolment(Base):
    """Enrolment model."""

    __tablename__ = "enrolments"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), primary_key=True)
    status: Mapped[EnrolmentStatus] = mapped_column(
        SQLEnum(EnrolmentStatus),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="enrolments")
    course: Mapped["Course"] = relationship("Course", back_populates="enrolments")

    def __repr__(self) -> str:
        return f"<Enrolment {self.user_id} -> {self.course_id}>" 