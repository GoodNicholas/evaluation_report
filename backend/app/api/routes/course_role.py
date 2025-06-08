from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.models.course_role import CourseRoleEnum

router = APIRouter()

@router.get("/{course_id}/roles", response_model=List[schemas.CourseRole])
def get_course_roles(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    current_role: models.CourseRole = Depends(
        lambda: deps.require_course_role(course_id=course_id, required_role=CourseRoleEnum.ASSISTANT)
    ),
):
    """
    Get all roles for a course.
    Only course owners, teachers, and assistants can view roles.
    """
    return crud.course_role.get_course_roles(db, course_id=course_id)

@router.post("/{course_id}/roles", response_model=schemas.CourseRole)
def create_course_role(
    course_id: int,
    role_in: schemas.CourseRoleCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    current_role: models.CourseRole = Depends(
        lambda: deps.require_course_role(course_id=course_id, required_role=CourseRoleEnum.OWNER)
    ),
):
    """
    Create a new role for a course.
    Only course owners can create roles.
    """
    # Check if user already has a role in the course
    existing_role = crud.course_role.get_by_course_and_user(
        db, course_id=course_id, user_id=role_in.user_id
    )
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a role in this course",
        )
    
    return crud.course_role.create_with_course(
        db, obj_in=role_in, course_id=course_id
    )

@router.put("/{course_id}/roles/{user_id}", response_model=schemas.CourseRole)
def update_course_role(
    course_id: int,
    user_id: int,
    role_in: schemas.CourseRoleUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    current_role: models.CourseRole = Depends(
        lambda: deps.require_course_role(course_id=course_id, required_role=CourseRoleEnum.OWNER)
    ),
):
    """
    Update a role for a course.
    Only course owners can update roles.
    """
    role = crud.course_role.get_by_course_and_user(
        db, course_id=course_id, user_id=user_id
    )
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    return crud.course_role.update(db, db_obj=role, obj_in=role_in)

@router.delete("/{course_id}/roles/{user_id}", response_model=schemas.CourseRole)
def delete_course_role(
    course_id: int,
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    current_role: models.CourseRole = Depends(
        lambda: deps.require_course_role(course_id=course_id, required_role=CourseRoleEnum.OWNER)
    ),
):
    """
    Delete a role from a course.
    Only course owners can delete roles.
    """
    role = crud.course_role.get_by_course_and_user(
        db, course_id=course_id, user_id=user_id
    )
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    return crud.course_role.remove_role(db, course_id=course_id, user_id=user_id) 