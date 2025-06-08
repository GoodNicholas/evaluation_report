import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.config import settings
from app.models.course_role import CourseRoleEnum
from tests.utils.course import create_random_course
from tests.utils.user import create_random_user, get_superuser_token_headers
from tests.utils.utils import random_lower_string

def test_create_course_role(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    # Create a course owner
    owner = create_random_user(db)
    course = create_random_course(db, owner_id=owner.id)
    
    # Create a user to assign a role to
    user = create_random_user(db)
    
    data = {
        "user_id": user.id,
        "role": CourseRoleEnum.TEACHER
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/courses/{course.id}/roles",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["user_id"] == user.id
    assert content["role"] == CourseRoleEnum.TEACHER
    assert content["course_id"] == course.id

def test_get_course_roles(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    # Create a course owner
    owner = create_random_user(db)
    course = create_random_course(db, owner_id=owner.id)
    
    # Create and assign roles
    teacher = create_random_user(db)
    assistant = create_random_user(db)
    
    crud.course_role.create_with_course(
        db,
        obj_in=schemas.CourseRoleCreate(user_id=teacher.id, role=CourseRoleEnum.TEACHER),
        course_id=course.id
    )
    crud.course_role.create_with_course(
        db,
        obj_in=schemas.CourseRoleCreate(user_id=assistant.id, role=CourseRoleEnum.ASSISTANT),
        course_id=course.id
    )
    
    response = client.get(
        f"{settings.API_V1_STR}/courses/{course.id}/roles",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) == 3  # owner + teacher + assistant
    roles = {item["user_id"]: item["role"] for item in content}
    assert roles[owner.id] == CourseRoleEnum.OWNER
    assert roles[teacher.id] == CourseRoleEnum.TEACHER
    assert roles[assistant.id] == CourseRoleEnum.ASSISTANT

def test_update_course_role(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    # Create a course owner
    owner = create_random_user(db)
    course = create_random_course(db, owner_id=owner.id)
    
    # Create and assign a role
    user = create_random_user(db)
    role = crud.course_role.create_with_course(
        db,
        obj_in=schemas.CourseRoleCreate(user_id=user.id, role=CourseRoleEnum.ASSISTANT),
        course_id=course.id
    )
    
    data = {"role": CourseRoleEnum.TEACHER}
    response = client.put(
        f"{settings.API_V1_STR}/courses/{course.id}/roles/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["user_id"] == user.id
    assert content["role"] == CourseRoleEnum.TEACHER
    assert content["course_id"] == course.id

def test_delete_course_role(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    # Create a course owner
    owner = create_random_user(db)
    course = create_random_course(db, owner_id=owner.id)
    
    # Create and assign a role
    user = create_random_user(db)
    role = crud.course_role.create_with_course(
        db,
        obj_in=schemas.CourseRoleCreate(user_id=user.id, role=CourseRoleEnum.TEACHER),
        course_id=course.id
    )
    
    response = client.delete(
        f"{settings.API_V1_STR}/courses/{course.id}/roles/{user.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["user_id"] == user.id
    assert content["role"] == CourseRoleEnum.TEACHER
    assert content["course_id"] == course.id
    
    # Verify role is deleted
    role = crud.course_role.get_by_course_and_user(
        db, course_id=course.id, user_id=user.id
    )
    assert role is None

def test_cannot_delete_owner_role(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    # Create a course owner
    owner = create_random_user(db)
    course = create_random_course(db, owner_id=owner.id)
    
    response = client.delete(
        f"{settings.API_V1_STR}/courses/{course.id}/roles/{owner.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 400
    assert "Cannot delete owner role" in response.json()["detail"]

def test_teacher_cannot_manage_roles(
    client: TestClient, db: Session
) -> None:
    # Create a course owner and teacher
    owner = create_random_user(db)
    teacher = create_random_user(db)
    course = create_random_course(db, owner_id=owner.id)
    
    # Assign teacher role
    crud.course_role.create_with_course(
        db,
        obj_in=schemas.CourseRoleCreate(user_id=teacher.id, role=CourseRoleEnum.TEACHER),
        course_id=course.id
    )
    
    # Get teacher token
    teacher_token_headers = {"Authorization": f"Bearer {teacher.id}"}
    
    # Try to create a role
    data = {
        "user_id": create_random_user(db).id,
        "role": CourseRoleEnum.ASSISTANT
    }
    response = client.post(
        f"{settings.API_V1_STR}/courses/{course.id}/roles",
        headers=teacher_token_headers,
        json=data,
    )
    assert response.status_code == 403
    
    # Try to update a role
    response = client.put(
        f"{settings.API_V1_STR}/courses/{course.id}/roles/{teacher.id}",
        headers=teacher_token_headers,
        json={"role": CourseRoleEnum.OWNER},
    )
    assert response.status_code == 403
    
    # Try to delete a role
    response = client.delete(
        f"{settings.API_V1_STR}/courses/{course.id}/roles/{teacher.id}",
        headers=teacher_token_headers,
    )
    assert response.status_code == 403

def test_assistant_can_view_roles_but_not_manage(
    client: TestClient, db: Session
) -> None:
    # Create a course owner and assistant
    owner = create_random_user(db)
    assistant = create_random_user(db)
    course = create_random_course(db, owner_id=owner.id)
    
    # Assign assistant role
    crud.course_role.create_with_course(
        db,
        obj_in=schemas.CourseRoleCreate(user_id=assistant.id, role=CourseRoleEnum.ASSISTANT),
        course_id=course.id
    )
    
    # Get assistant token
    assistant_token_headers = {"Authorization": f"Bearer {assistant.id}"}
    
    # Can view roles
    response = client.get(
        f"{settings.API_V1_STR}/courses/{course.id}/roles",
        headers=assistant_token_headers,
    )
    assert response.status_code == 200
    
    # Cannot create role
    data = {
        "user_id": create_random_user(db).id,
        "role": CourseRoleEnum.ASSISTANT
    }
    response = client.post(
        f"{settings.API_V1_STR}/courses/{course.id}/roles",
        headers=assistant_token_headers,
        json=data,
    )
    assert response.status_code == 403
    
    # Cannot update role
    response = client.put(
        f"{settings.API_V1_STR}/courses/{course.id}/roles/{assistant.id}",
        headers=assistant_token_headers,
        json={"role": CourseRoleEnum.TEACHER},
    )
    assert response.status_code == 403
    
    # Cannot delete role
    response = client.delete(
        f"{settings.API_V1_STR}/courses/{course.id}/roles/{assistant.id}",
        headers=assistant_token_headers,
    )
    assert response.status_code == 403 