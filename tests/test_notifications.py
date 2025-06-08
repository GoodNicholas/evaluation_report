from __future__ import annotations

import json
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.course import Course, Enrolment, EnrolmentStatus
from app.models.message import Dialog, Message
from app.models.notification import Notification, NotificationType
from app.models.role import Role
from app.models.user import User


@pytest.fixture
async def teacher(db: AsyncSession) -> User:
    """Create a teacher user."""
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
    return teacher


@pytest.fixture
async def student(db: AsyncSession) -> User:
    """Create a student user."""
    student_role = Role(name="student")
    db.add(student_role)
    student = User(
        email="student@example.com",
        first_name="Test",
        last_name="Student",
        password_hash=get_password_hash("password123"),
    )
    student.roles.append(student_role)
    db.add(student)
    await db.commit()
    return student


@pytest.fixture
async def course(db: AsyncSession, teacher: User) -> Course:
    """Create a course."""
    course = Course(
        title="Test Course",
        code="TEST101",
        description="Test course description",
        owner_id=teacher.id,
    )
    db.add(course)
    await db.commit()
    return course


@pytest.fixture
async def enrolment(db: AsyncSession, course: Course, student: User) -> Enrolment:
    """Create an enrolment."""
    enrolment = Enrolment(
        user_id=student.id,
        course_id=course.id,
        status=EnrolmentStatus.ACTIVE,
    )
    db.add(enrolment)
    await db.commit()
    return enrolment


@pytest.mark.asyncio
async def test_get_notifications(
    async_client: AsyncClient,
    db: AsyncSession,
    teacher: User,
    student: User,
) -> None:
    """Test getting notifications."""
    # Create notifications
    notifications = [
        Notification(
            user_id=student.id,
            type=NotificationType.NEW_GRADE,
            payload={"course_id": 1, "assignment_id": 1, "score": 85},
        ),
        Notification(
            user_id=student.id,
            type=NotificationType.NEW_MESSAGE,
            payload={"dialog_id": 1, "sender_id": teacher.id, "message_id": 1},
        ),
    ]
    for notification in notifications:
        db.add(notification)
    await db.commit()

    # Login as student
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "student@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Get notifications
    response = await async_client.get(
        "/me/notifications",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["type"] == "new_message"
    assert data[1]["type"] == "new_grade"


@pytest.mark.asyncio
async def test_update_notification(
    async_client: AsyncClient,
    db: AsyncSession,
    teacher: User,
    student: User,
) -> None:
    """Test updating notification."""
    # Create notification
    notification = Notification(
        user_id=student.id,
        type=NotificationType.NEW_GRADE,
        payload={"course_id": 1, "assignment_id": 1, "score": 85},
    )
    db.add(notification)
    await db.commit()

    # Login as student
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "student@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Update notification
    update_data = {"delivered": True}
    response = await async_client.patch(
        f"/notifications/{notification.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["delivered"] is True


@pytest.mark.asyncio
async def test_update_foreign_notification(
    async_client: AsyncClient,
    db: AsyncSession,
    teacher: User,
    student: User,
) -> None:
    """Test updating another user's notification."""
    # Create notification for student
    notification = Notification(
        user_id=student.id,
        type=NotificationType.NEW_GRADE,
        payload={"course_id": 1, "assignment_id": 1, "score": 85},
    )
    db.add(notification)
    await db.commit()

    # Login as teacher
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "teacher@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Try to update notification
    update_data = {"delivered": True}
    response = await async_client.patch(
        f"/notifications/{notification.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_websocket_notifications(
    async_client: AsyncClient,
    db: AsyncSession,
    teacher: User,
    student: User,
) -> None:
    """Test WebSocket notifications."""
    # Login as student
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "student@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Connect to WebSocket
    async with async_client.websocket_connect(
        f"/ws/notifications?token={access_token}"
    ) as websocket:
        # Create notification
        notification = Notification(
            user_id=student.id,
            type=NotificationType.NEW_GRADE,
            payload={"course_id": 1, "assignment_id": 1, "score": 85},
        )
        db.add(notification)
        await db.commit()

        # Send notification via WebSocket
        await notification_service.manager.send_notification(student.id, notification)

        # Receive notification
        response = await websocket.receive_json()
        assert response["type"] == "new_grade"
        assert response["payload"]["score"] == 85 