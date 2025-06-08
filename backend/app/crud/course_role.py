from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.course_role import CourseRole, CourseRoleEnum
from app.schemas.course_role import CourseRoleCreate, CourseRoleUpdate

class CRUDCourseRole(CRUDBase[CourseRole, CourseRoleCreate, CourseRoleUpdate]):
    def get_by_course_and_user(
        self, db: Session, *, course_id: int, user_id: int
    ) -> Optional[CourseRole]:
        return db.query(CourseRole).filter(
            CourseRole.course_id == course_id,
            CourseRole.user_id == user_id
        ).first()

    def get_course_roles(
        self, db: Session, *, course_id: int, skip: int = 0, limit: int = 100
    ) -> List[CourseRole]:
        return db.query(CourseRole).filter(
            CourseRole.course_id == course_id
        ).offset(skip).limit(limit).all()

    def create_with_course(
        self, db: Session, *, obj_in: CourseRoleCreate, course_id: int
    ) -> CourseRole:
        db_obj = CourseRole(
            course_id=course_id,
            user_id=obj_in.user_id,
            role=obj_in.role
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove_role(
        self, db: Session, *, course_id: int, user_id: int
    ) -> Optional[CourseRole]:
        obj = db.query(CourseRole).filter(
            CourseRole.course_id == course_id,
            CourseRole.user_id == user_id
        ).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

course_role = CRUDCourseRole(CourseRole) 