from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

# Association table for assignments and students
assignment_student = Table(
    "assignment_student",
    Base.metadata,
    Column("assignment_id", Integer, ForeignKey("assignments.id"), primary_key=True),
    Column("student_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("score", Integer, nullable=True),
    Column("created_at", DateTime, server_default=text("now()")),
    Column("updated_at", DateTime, server_default=text("now()"), onupdate=text("now()")),
)


class Assignment(Base):
    """Assignment model."""
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    max_score: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("now()"), onupdate=text("now()")
    )

    # Relationships
    course = relationship("Course", back_populates="assignments")
    students = relationship(
        "User",
        secondary=assignment_student,
        back_populates="assignments",
    )


# SQL View for gradebook
gradebook_view = text("""
CREATE OR REPLACE VIEW v_gradebook AS
SELECT 
    a.course_id,
    u.id as student_id,
    a.id as assignment_id,
    as2.score
FROM assignments a
CROSS JOIN users u
LEFT JOIN assignment_student as2 ON as2.assignment_id = a.id AND as2.student_id = u.id
JOIN enrolments e ON e.user_id = u.id AND e.course_id = a.course_id
WHERE e.status = 'active'
""") 