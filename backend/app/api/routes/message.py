from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.message import DialogWithMessages, MessageCreate, MessageInDB
from app.services import message as message_service

router = APIRouter()


@router.get("/dialogs/{dialog_id}/messages", response_model=list[MessageInDB])
async def get_messages(
    dialog_id: int,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MessageInDB]:
    """Get messages for a dialog."""
    messages = await message_service.get_messages(db, dialog_id, skip, limit)
    return messages


@router.post("/dialogs/{dialog_id}/messages", response_model=MessageInDB)
async def create_message(
    dialog_id: int,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageInDB:
    """Create a new message in a dialog."""
    db_message = await message_service.create_message(
        db, dialog_id, current_user.id, message
    )
    return db_message


@router.websocket("/ws/chat/{dialog_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    dialog_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """WebSocket endpoint for real-time chat."""
    try:
        await message_service.handle_websocket(websocket, db, current_user, dialog_id)
    except WebSocketDisconnect:
        pass 