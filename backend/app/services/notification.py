from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationCreate, NotificationUpdate


async def create_notification(
    db: AsyncSession,
    notification: NotificationCreate,
) -> Notification:
    """Create a new notification."""
    db_notification = Notification(**notification.dict())
    db.add(db_notification)
    await db.commit()
    await db.refresh(db_notification)
    return db_notification


async def get_notifications(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Notification]:
    """Get notifications for a user."""
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_notification(
    db: AsyncSession,
    notification_id: int,
    notification: NotificationUpdate,
) -> Notification:
    """Update a notification."""
    db_notification = await db.get(Notification, notification_id)
    if not db_notification:
        return None

    for field, value in notification.dict(exclude_unset=True).items():
        setattr(db_notification, field, value)

    await db.commit()
    await db.refresh(db_notification)
    return db_notification


async def mark_notifications_as_delivered(
    db: AsyncSession,
    user_id: int,
) -> None:
    """Mark all undelivered notifications as delivered for a user."""
    stmt = select(Notification).where(
        Notification.user_id == user_id,
        Notification.delivered == False,
    )
    result = await db.execute(stmt)
    notifications = result.scalars().all()

    for notification in notifications:
        notification.delivered = True

    await db.commit()


# Event handlers
async def handle_new_grade(
    db: AsyncSession,
    user_id: int,
    course_id: int,
    assignment_id: int,
    score: float,
) -> None:
    """Handle new grade event."""
    notification = NotificationCreate(
        user_id=user_id,
        type=NotificationType.NEW_GRADE,
        payload={
            "course_id": course_id,
            "assignment_id": assignment_id,
            "score": score,
        },
    )
    await create_notification(db, notification)


async def handle_new_message(
    db: AsyncSession,
    user_id: int,
    dialog_id: int,
    sender_id: int,
    message_id: int,
) -> None:
    """Handle new message event."""
    notification = NotificationCreate(
        user_id=user_id,
        type=NotificationType.NEW_MESSAGE,
        payload={
            "dialog_id": dialog_id,
            "sender_id": sender_id,
            "message_id": message_id,
        },
    )
    await create_notification(db, notification)


async def handle_submission_status(
    db: AsyncSession,
    user_id: int,
    submission_id: int,
    status: str,
) -> None:
    """Handle submission status change event."""
    notification = NotificationCreate(
        user_id=user_id,
        type=NotificationType.SUBMISSION_STATUS,
        payload={
            "submission_id": submission_id,
            "status": status,
        },
    )
    await create_notification(db, notification)


# WebSocket connection manager
class ConnectionManager:
    """WebSocket connection manager."""

    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """Connect a new WebSocket."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        """Disconnect a WebSocket."""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_notification(self, user_id: int, notification: Notification) -> None:
        """Send notification to all user's WebSocket connections."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(notification.dict())
                except Exception:
                    # Remove failed connection
                    self.disconnect(connection, user_id)


# Global connection manager
manager = ConnectionManager()


async def handle_websocket(
    websocket: WebSocket,
    user_id: int,
) -> None:
    """Handle WebSocket connection for notifications."""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket, user_id) 