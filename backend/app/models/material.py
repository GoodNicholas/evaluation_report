from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Material(Base):
    """Material model."""

    __tablename__ = "materials"

    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    uploader_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    stored_path: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="materials")
    uploader: Mapped["User"] = relationship("User", back_populates="uploaded_materials")

    def __repr__(self) -> str:
        return f"<Material {self.filename}>" 