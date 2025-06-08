from __future__ import annotations

import os
from io import BytesIO

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.course import Course, Enrolment, EnrolmentStatus
from app.models.role import Role
from app.models.user import User
from app.schemas.course import CourseCreate


@pytest.mark.asyncio
async def test_create_course(
    async_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test creating a course."""
    # Create teacher role and user
    teacher_role = Role(name="teacher")
    db.add(teacher_role)
    teacher = User(
        email="teacher@example.com",
        first_name="Test",
        last_name="Teacher",
        password_hash=get_password_hash("password123"),
    )
    teacher.roles.append(teacher_role)
    db.add(teacher)
    await db.commit()

    # Login as teacher
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "teacher@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Create course
    course_in = CourseCreate(
        title="Test Course",
        code="TEST101",
        description="Test course description",
    )
    response = await async_client.post(
        "/courses",
        json=course_in.dict(),
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == course_in.title
    assert data["code"] == course_in.code
    assert data["description"] == course_in.description
    assert data["owner_id"] == teacher.id


@pytest.mark.asyncio
async def test_get_course(
    async_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test getting a course."""
    # Create course
    course = Course(
        title="Test Course",
        code="TEST101",
        description="Test course description",
        owner_id=1,  # Assuming user with ID 1 exists
    )
    db.add(course)
    await db.commit()

    # Create student
    student = User(
        email="student@example.com",
        first_name="Test",
        last_name="Student",
        password_hash=get_password_hash("password123"),
    )
    db.add(student)
    await db.commit()

    # Enroll student
    enrolment = Enrolment(
        user_id=student.id,
        course_id=course.id,
        status=EnrolmentStatus.ACTIVE,
    )
    db.add(enrolment)
    await db.commit()

    # Login as student
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "student@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Get course
    response = await async_client.get(
        f"/courses/{course.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == course.title
    assert data["code"] == course.code
    assert data["description"] == course.description
    assert data["enrolment_status"] == EnrolmentStatus.ACTIVE


@pytest.mark.asyncio
async def test_upload_material(
    async_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test uploading course material."""
    # Create course
    course = Course(
        title="Test Course",
        code="TEST101",
        description="Test course description",
        owner_id=1,  # Assuming user with ID 1 exists
    )
    db.add(course)
    await db.commit()

    # Create teacher
    teacher_role = Role(name="teacher")
    db.add(teacher_role)
    teacher = User(
        email="teacher@example.com",
        first_name="Test",
        last_name="Teacher",
        password_hash=get_password_hash("password123"),
    )
    teacher.roles.append(teacher_role)
    db.add(teacher)
    await db.commit()

    # Login as teacher
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "teacher@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Create test file
    file_content = b"Test file content"
    files = {
        "file": (
            "test.txt",
            BytesIO(file_content),
            "text/plain",
        )
    }

    # Upload material
    response = await async_client.post(
        f"/courses/{course.id}/materials",
        files=files,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["mime_type"] == "text/plain"
    assert data["size"] == len(file_content)
    assert data["course_id"] == course.id
    assert data["uploader_id"] == teacher.id

    # Verify file exists
    assert os.path.exists(data["stored_path"])


@pytest.mark.asyncio
async def test_list_materials(
    async_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test listing course materials."""
    # Create course
    course = Course(
        title="Test Course",
        code="TEST101",
        description="Test course description",
        owner_id=1,  # Assuming user with ID 1 exists
    )
    db.add(course)
    await db.commit()

    # Create student
    student = User(
        email="student@example.com",
        first_name="Test",
        last_name="Student",
        password_hash=get_password_hash("password123"),
    )
    db.add(student)
    await db.commit()

    # Enroll student
    enrolment = Enrolment(
        user_id=student.id,
        course_id=course.id,
        status=EnrolmentStatus.ACTIVE,
    )
    db.add(enrolment)
    await db.commit()

    # Login as student
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "student@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # List materials
    response = await async_client.get(
        f"/courses/{course.id}/materials",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) 