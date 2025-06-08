from __future__ import annotations

import hashlib
import hmac
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.config import get_settings
from app.db.session import get_db
from app.models.course import Course, Enrolment, EnrolmentStatus
from app.models.material import Material
from app.models.user import User
from app.schemas.course import Course as CourseSchema
from app.schemas.course import CourseCreate, CourseUpdate, Enrolment as EnrolmentSchema
from app.schemas.material import Material as MaterialSchema, MaterialList
from app.services import courses

settings = get_settings()
router = APIRouter()

def generate_signed_url(material_id: int, expires_in: int = 3600) -> str:
    """Generate a signed URL for material download."""
    expires_at = int(time.time()) + expires_in
    message = f"{material_id}:{expires_at}".encode()
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        message,
        hashlib.sha256
    ).hexdigest()
    return f"/materials/{material_id}/download?expires={expires_at}&signature={signature}"


@router.post("", response_model=CourseSchema, status_code=status.HTTP_201_CREATED)
async def create_course(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("teacher"))],
    course_in: CourseCreate,
) -> CourseSchema:
    """Create new course."""
    return await courses.create_course(db, current_user, course_in)


@router.get("/{course_id}", response_model=CourseSchema)
async def get_course(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    course_id: int,
) -> CourseSchema:
    """Get course by ID."""
    return await courses.get_course(db, current_user, course_id)


@router.post(
    "/{course_id}/materials",
    response_model=MaterialSchema,
    status_code=status.HTTP_201_CREATED,
)
async def upload_material(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    course_id: int,
    file: Annotated[UploadFile, File()],
) -> MaterialSchema:
    """Upload course material."""
    return await courses.upload_material(db, current_user, course_id, file)


@router.get("/{course_id}/materials", response_model=MaterialList)
async def list_materials(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    course_id: int,
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
) -> MaterialList:
    """List course materials with cursor-based pagination."""
    materials, next_cursor, has_more = await courses.list_materials(
        db, current_user, course_id, cursor, limit
    )
    return MaterialList(
        items=materials,
        next_cursor=next_cursor,
        has_more=has_more
    )


@router.patch("/{course_id}", response_model=CourseSchema)
async def update_course(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    course_id: int,
    course_in: CourseUpdate,
) -> CourseSchema:
    """Update course."""
    return await courses.update_course(db, current_user, course_id, course_in)
