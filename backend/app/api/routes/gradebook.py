from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.gradebook import Gradebook, GradebookUpdate
from app.services import gradebook

router = APIRouter()


@router.get("/{course_id}/gradebook", response_model=Gradebook)
async def get_gradebook(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    course_id: int,
) -> Gradebook:
    """Get gradebook for a course."""
    return await gradebook.get_gradebook(db, current_user, course_id)


@router.patch("/{course_id}/gradebook")
async def update_gradebook(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("teacher"))],
    course_id: int,
    update: GradebookUpdate,
) -> None:
    """Update gradebook scores."""
    await gradebook.update_gradebook(db, current_user, course_id, update)


@router.websocket("/ws/gradebook/{course_id}")
async def websocket_gradebook(
    websocket: WebSocket,
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """WebSocket endpoint for gradebook updates."""
    await websocket.accept()
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass 