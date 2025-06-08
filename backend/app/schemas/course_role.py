from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.course_role import CourseRoleEnum

class CourseRoleBase(BaseModel):
    role: CourseRoleEnum

class CourseRoleCreate(CourseRoleBase):
    user_id: int

class CourseRoleUpdate(CourseRoleBase):
    pass

class CourseRoleInDBBase(CourseRoleBase):
    id: int
    course_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CourseRole(CourseRoleInDBBase):
    pass

class CourseRoleInDB(CourseRoleInDBBase):
    pass 