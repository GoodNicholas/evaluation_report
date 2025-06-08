from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import bleach
from fastapi import HTTPException, WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.redis import get_redis
from app.models.course import Course, Enrolment, EnrolmentStatus
from app.models.message import Dialog, Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageUpdate


async def get_dialog(
    db: AsyncSession,
    course_id: int,
    teacher_id: int,
    student_id: int,
) -> Optional[Dialog]:
    """Get dialog between teacher and student for a course."""
    stmt = (
        select(Dialog)
        .where(
            Dialog.course_id == course_id,
            Dialog.teacher_id == teacher_id,
            Dialog.student_id == student_id,
        )
        .options(selectinload(Dialog.messages))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_dialog(
    db: AsyncSession,
    course_id: int,
    teacher_id: int,
    student_id: int,
) -> Dialog:
    """Create a new dialog between teacher and student for a course."""
    # Verify course exists and user is enrolled
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify student is enrolled in course
    stmt = select(Enrolment).where(
        Enrolment.course_id == course_id,
        Enrolment.user_id == student_id,
        Enrolment.status == EnrolmentStatus.ACTIVE,
    )
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=403, detail="Student is not enrolled in this course"
        )

    # Create dialog
    dialog = Dialog(
        course_id=course_id,
        teacher_id=teacher_id,
        student_id=student_id,
    )
    db.add(dialog)
    await db.commit()
    await db.refresh(dialog)
    return dialog


async def get_or_create_dialog(
    db: AsyncSession,
    course_id: int,
    teacher_id: int,
    student_id: int,
) -> Dialog:
    """Get existing dialog or create new one."""
    dialog = await get_dialog(db, course_id, teacher_id, student_id)
    if not dialog:
        dialog = await create_dialog(db, course_id, teacher_id, student_id)
    return dialog


async def get_messages(
    db: AsyncSession,
    dialog_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Message]:
    """Get messages for a dialog."""
    stmt = (
        select(Message)
        .where(Message.dialog_id == dialog_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_message(
    db: AsyncSession,
    dialog_id: int,
    sender_id: int,
    message: MessageCreate,
) -> Message:
    """Create a new message in a dialog."""
    # Get dialog
    dialog = await db.get(Dialog, dialog_id)
    if not dialog:
        raise HTTPException(status_code=404, detail="Dialog not found")

    # Verify sender is part of dialog
    if sender_id not in (dialog.teacher_id, dialog.student_id):
        raise HTTPException(status_code=403, detail="Not authorized to send messages")

    # Rate limiting
    redis = await get_redis()
    key = f"message_rate:{sender_id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)  # 60 seconds window
    if count > 5:  # 5 messages per minute
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Please try again later."
        )

    # Sanitize message body (allow only safe markdown subset)
    allowed_tags = ["p", "br", "b", "i", "em", "strong", "a"]
    allowed_attrs = {"a": ["href", "title"]}
    sanitized_body = bleach.clean(
        message.body,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True,
    )

    # Create message
    db_message = Message(
        dialog_id=dialog_id,
        sender_id=sender_id,
        body=sanitized_body,
    )
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message


async def update_message(
    db: AsyncSession,
    message_id: int,
    message: MessageUpdate,
) -> Message:
    """Update a message."""
    db_message = await db.get(Message, message_id)
    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")

    for field, value in message.dict(exclude_unset=True).items():
        setattr(db_message, field, value)

    await db.commit()
    await db.refresh(db_message)
    return db_message


async def mark_messages_as_read(
    db: AsyncSession,
    dialog_id: int,
    user_id: int,
) -> None:
    """Mark all unread messages in dialog as read for user."""
    stmt = (
        select(Message)
        .where(
            Message.dialog_id == dialog_id,
            Message.sender_id != user_id,
            Message.read == False,
        )
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    for message in messages:
        message.read = True

    await db.commit()


async def handle_websocket(
    websocket: WebSocket,
    db: AsyncSession,
    user: User,
    dialog_id: int,
) -> None:
    """Handle websocket connection for chat."""
    # Get dialog
    dialog = await db.get(Dialog, dialog_id)
    if not dialog:
        await websocket.close(code=4004)
        return

    # Verify user is part of dialog
    if user.id not in (dialog.teacher_id, dialog.student_id):
        await websocket.close(code=4003)
        return

    await websocket.accept()

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = MessageCreate(**data)

            # Create message
            db_message = await create_message(db, dialog_id, user.id, message)

            # Mark other messages as read
            await mark_messages_as_read(db, dialog_id, user.id)

            # Send message back
            await websocket.send_json(db_message.dict())

    except Exception as e:
        await websocket.close(code=1011)
        raise e 