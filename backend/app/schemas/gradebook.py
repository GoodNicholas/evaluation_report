from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AssignmentBase(BaseModel):
    """Base assignment schema."""
    title: str
    description: Optional[str] = None
    max_score: int = Field(default=100, ge=0, le=100)


class AssignmentCreate(AssignmentBase):
    """Assignment creation schema."""
    pass


class Assignment(AssignmentBase):
    """Assignment schema."""
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GradebookCell(BaseModel):
    """Gradebook cell schema."""
    student_id: int
    assignment_id: int
    score: Optional[int] = None


class GradebookUpdate(BaseModel):
    """Gradebook update schema."""
    updates: list[GradebookCell]


class GradebookRow(BaseModel):
    """Gradebook row schema."""
    student_id: int
    student_name: str
    scores: dict[int, Optional[int]]  # assignment_id -> score


class Gradebook(BaseModel):
    """Gradebook schema."""
    assignments: list[Assignment]
    rows: list[GradebookRow] 