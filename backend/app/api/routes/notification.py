from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.notification import NotificationInDB, NotificationUpdate
from app.services import notification as notification_service

router = APIRouter()


@router.get("/me/notifications", response_model=list[NotificationInDB])
async def get_notifications(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationInDB]:
    """Get notifications for current user."""
    notifications = await notification_service.get_notifications(
        db, current_user.id, skip, limit
    )
    return notifications


@router.patch("/notifications/{notification_id}", response_model=NotificationInDB)
async def update_notification(
    notification_id: int,
    notification: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationInDB:
    """Update a notification."""
    db_notification = await notification_service.update_notification(
        db, notification_id, notification
    )
    if not db_notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if db_notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update notification")
    return db_notification


@router.websocket("/ws/notifications")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user),
) -> None:
    """WebSocket endpoint for real-time notifications."""
    try:
        await notification_service.handle_websocket(websocket, current_user.id)
    except WebSocketDisconnect:
        pass 