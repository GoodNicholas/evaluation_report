from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base

class CourseRoleEnum(str, enum.Enum):
    OWNER = "owner"
    TEACHER = "teacher"
    ASSISTANT = "assistant"

class CourseRole(Base):
    __tablename__ = "course_roles"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(CourseRoleEnum), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="roles")
    user = relationship("User", back_populates="course_roles") 