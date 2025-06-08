from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.assignment import Assignment
from app.models.course import Course, Enrolment, EnrolmentStatus
from app.models.role import Role
from app.models.user import User
from app.schemas.gradebook import AssignmentCreate


@pytest.mark.asyncio
async def test_get_gradebook_teacher(
    async_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test getting gradebook as teacher."""
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

    # Create course
    course = Course(
        title="Test Course",
        code="TEST101",
        description="Test course description",
        owner_id=teacher.id,
    )
    db.add(course)
    await db.commit()

    # Create assignments
    assignments = [
        Assignment(
            course_id=course.id,
            title=f"Assignment {i}",
            description=f"Description {i}",
            max_score=100,
        )
        for i in range(3)
    ]
    for assignment in assignments:
        db.add(assignment)
    await db.commit()

    # Create students
    students = []
    for i in range(3):
        student = User(
            email=f"student{i}@example.com",
            first_name=f"Student{i}",
            last_name="Test",
            password_hash=get_password_hash("password123"),
        )
        db.add(student)
        students.append(student)
    await db.commit()

    # Enroll students
    for student in students:
        enrolment = Enrolment(
            user_id=student.id,
            course_id=course.id,
            status=EnrolmentStatus.ACTIVE,
        )
        db.add(enrolment)
    await db.commit()

    # Login as teacher
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "teacher@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Get gradebook
    response = await async_client.get(
        f"/courses/{course.id}/gradebook",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["assignments"]) == 3
    assert len(data["rows"]) == 3
    for row in data["rows"]:
        assert len(row["scores"]) == 3
        for score in row["scores"].values():
            assert score is None


@pytest.mark.asyncio
async def test_get_gradebook_student(
    async_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test getting gradebook as student."""
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

    # Create course
    course = Course(
        title="Test Course",
        code="TEST101",
        description="Test course description",
        owner_id=teacher.id,
    )
    db.add(course)
    await db.commit()

    # Create assignment
    assignment = Assignment(
        course_id=course.id,
        title="Test Assignment",
        description="Test description",
        max_score=100,
    )
    db.add(assignment)
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

    # Get gradebook
    response = await async_client.get(
        f"/courses/{course.id}/gradebook",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["assignments"]) == 1
    assert len(data["rows"]) == 1
    assert data["rows"][0]["student_id"] == student.id
    assert len(data["rows"][0]["scores"]) == 1
    assert data["rows"][0]["scores"][str(assignment.id)] is None


@pytest.mark.asyncio
async def test_update_gradebook(
    async_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test updating gradebook."""
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

    # Create course
    course = Course(
        title="Test Course",
        code="TEST101",
        description="Test course description",
        owner_id=teacher.id,
    )
    db.add(course)
    await db.commit()

    # Create assignment
    assignment = Assignment(
        course_id=course.id,
        title="Test Assignment",
        description="Test description",
        max_score=100,
    )
    db.add(assignment)
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

    # Login as teacher
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "teacher@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Update gradebook
    update_data = {
        "updates": [
            {
                "student_id": student.id,
                "assignment_id": assignment.id,
                "score": 85,
            }
        ]
    }
    response = await async_client.patch(
        f"/courses/{course.id}/gradebook",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200

    # Verify update
    response = await async_client.get(
        f"/courses/{course.id}/gradebook",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["rows"]) == 1
    assert data["rows"][0]["scores"][str(assignment.id)] == 85


@pytest.mark.asyncio
async def test_update_gradebook_student_forbidden(
    async_client: AsyncClient,
    db: AsyncSession,
) -> None:
    """Test that students cannot update gradebook."""
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

    # Create course
    course = Course(
        title="Test Course",
        code="TEST101",
        description="Test course description",
        owner_id=teacher.id,
    )
    db.add(course)
    await db.commit()

    # Create assignment
    assignment = Assignment(
        course_id=course.id,
        title="Test Assignment",
        description="Test description",
        max_score=100,
    )
    db.add(assignment)
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

    # Try to update gradebook
    update_data = {
        "updates": [
            {
                "student_id": student.id,
                "assignment_id": assignment.id,
                "score": 85,
            }
        ]
    }
    response = await async_client.patch(
        f"/courses/{course.id}/gradebook",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 403 