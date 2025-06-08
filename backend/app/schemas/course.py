from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.models.course import EnrolmentStatus
from app.schemas.user import User


class CourseBase(BaseModel):
    """Base course schema."""

    title: str
    code: str
    description: str


class CourseCreate(CourseBase):
    """Course creation schema."""

    pass


class CourseUpdate(CourseBase):
    """Course update schema."""

    pass


class Course(CourseBase):
    """Course schema."""

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    owner: User
    enrolment_status: EnrolmentStatus | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class EnrolmentBase(BaseModel):
    """Base enrolment schema."""

    status: EnrolmentStatus


class EnrolmentCreate(EnrolmentBase):
    """Enrolment creation schema."""

    pass


class EnrolmentUpdate(EnrolmentBase):
    """Enrolment update schema."""

    pass


class Enrolment(EnrolmentBase):
    """Enrolment schema."""

    user_id: int
    course_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True 