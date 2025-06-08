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
async def test_create_dialog(
    async_client: AsyncClient,
    db: AsyncSession,
    teacher: User,
    student: User,
    course: Course,
    enrolment: Enrolment,
) -> None:
    """Test creating a dialog."""
    # Login as teacher
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "teacher@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Create message (this will create dialog)
    message_data = {"body": "Hello student!"}
    response = await async_client.post(
        f"/courses/{course.id}/messages",
        json=message_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200

    # Verify dialog was created
    stmt = select(Dialog).where(
        Dialog.course_id == course.id,
        Dialog.teacher_id == teacher.id,
        Dialog.student_id == student.id,
    )
    result = await db.execute(stmt)
    dialog = result.scalar_one_or_none()
    assert dialog is not None


@pytest.mark.asyncio
async def test_create_message(
    async_client: AsyncClient,
    db: AsyncSession,
    teacher: User,
    student: User,
    course: Course,
    enrolment: Enrolment,
) -> None:
    """Test creating a message."""
    # Create dialog
    dialog = Dialog(
        course_id=course.id,
        teacher_id=teacher.id,
        student_id=student.id,
    )
    db.add(dialog)
    await db.commit()

    # Login as teacher
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "teacher@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Create message
    message_data = {"body": "Hello student!"}
    response = await async_client.post(
        f"/dialogs/{dialog.id}/messages",
        json=message_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["body"] == "Hello student!"
    assert data["sender_id"] == teacher.id


@pytest.mark.asyncio
async def test_get_messages(
    async_client: AsyncClient,
    db: AsyncSession,
    teacher: User,
    student: User,
    course: Course,
    enrolment: Enrolment,
) -> None:
    """Test getting messages."""
    # Create dialog
    dialog = Dialog(
        course_id=course.id,
        teacher_id=teacher.id,
        student_id=student.id,
    )
    db.add(dialog)
    await db.commit()

    # Create messages
    messages = [
        Message(
            dialog_id=dialog.id,
            sender_id=teacher.id,
            body=f"Message {i}",
        )
        for i in range(3)
    ]
    for message in messages:
        db.add(message)
    await db.commit()

    # Login as teacher
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "teacher@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Get messages
    response = await async_client.get(
        f"/dialogs/{dialog.id}/messages",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    for i, message in enumerate(reversed(data)):
        assert message["body"] == f"Message {i}"


@pytest.mark.asyncio
async def test_rate_limit(
    async_client: AsyncClient,
    db: AsyncSession,
    teacher: User,
    student: User,
    course: Course,
    enrolment: Enrolment,
) -> None:
    """Test message rate limiting."""
    # Create dialog
    dialog = Dialog(
        course_id=course.id,
        teacher_id=teacher.id,
        student_id=student.id,
    )
    db.add(dialog)
    await db.commit()

    # Login as teacher
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "teacher@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Send 6 messages (should fail on 6th)
    for i in range(6):
        message_data = {"body": f"Message {i}"}
        response = await async_client.post(
            f"/dialogs/{dialog.id}/messages",
            json=message_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if i < 5:
            assert response.status_code == 200
        else:
            assert response.status_code == 429


@pytest.mark.asyncio
async def test_xss_protection(
    async_client: AsyncClient,
    db: AsyncSession,
    teacher: User,
    student: User,
    course: Course,
    enrolment: Enrolment,
) -> None:
    """Test XSS protection in messages."""
    # Create dialog
    dialog = Dialog(
        course_id=course.id,
        teacher_id=teacher.id,
        student_id=student.id,
    )
    db.add(dialog)
    await db.commit()

    # Login as teacher
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "teacher@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Create message with XSS attempt
    message_data = {
        "body": '<script>alert("XSS")</script><p>Safe text</p><a href="javascript:alert(1)">Click me</a>'
    }
    response = await async_client.post(
        f"/dialogs/{dialog.id}/messages",
        json=message_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "<script>" not in data["body"]
    assert "javascript:" not in data["body"]
    assert "<p>Safe text</p>" in data["body"]


@pytest.mark.asyncio
async def test_websocket_chat(
    async_client: AsyncClient,
    db: AsyncSession,
    teacher: User,
    student: User,
    course: Course,
    enrolment: Enrolment,
) -> None:
    """Test WebSocket chat."""
    # Create dialog
    dialog = Dialog(
        course_id=course.id,
        teacher_id=teacher.id,
        student_id=student.id,
    )
    db.add(dialog)
    await db.commit()

    # Login as teacher
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "teacher@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    # Connect to WebSocket
    async with async_client.websocket_connect(
        f"/ws/chat/{dialog.id}?token={access_token}"
    ) as websocket:
        # Send message
        message_data = {"body": "Hello via WebSocket!"}
        await websocket.send_json(message_data)

        # Receive message
        response = await websocket.receive_json()
        assert response["body"] == "Hello via WebSocket!"
        assert response["sender_id"] == teacher.id

        # Verify message was saved
        stmt = select(Message).where(Message.dialog_id == dialog.id)
        result = await db.execute(stmt)
        message = result.scalar_one_or_none()
        assert message is not None
        assert message.body == "Hello via WebSocket!" 