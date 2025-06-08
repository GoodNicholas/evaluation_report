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
from app.schemas.course import CourseCreate, Enrolment as EnrolmentSchema
from app.schemas.material import Material as MaterialSchema, MaterialList

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
) -> Course:
    """Create new course."""
    course = Course(
        title=course_in.title,
        code=course_in.code,
        description=course_in.description,
        owner_id=current_user.id,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


@router.get("/{course_id}", response_model=CourseSchema)
async def get_course(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    course_id: int,
) -> Course:
    """Get course by ID."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    # Get enrolment status
    result = await db.execute(
        select(Enrolment).where(
            Enrolment.course_id == course_id,
            Enrolment.user_id == current_user.id,
        )
    )
    enrolment = result.scalar_one_or_none()
    if enrolment:
        course.enrolment_status = enrolment.status

    return course


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
) -> Material:
    """Upload course material."""
    # Check course exists and user has access
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    if course.owner_id != current_user.id and not any(
        r.name == "teacher" for r in current_user.roles
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > 20 * 1024 * 1024:  # 20 MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large",
        )

    sha256 = hashlib.sha256(content).hexdigest()

    # Create storage directory
    os.makedirs(f"data/materials/{course_id}", exist_ok=True)

    # Save file
    ext = os.path.splitext(file.filename)[1]
    stored_path = f"data/materials/{course_id}/{uuid.uuid4()}{ext}"
    with open(stored_path, "wb") as f:
        f.write(content)

    # Create material record
    material = Material(
        course_id=course_id,
        uploader_id=current_user.id,
        filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        size=file_size,
        stored_path=stored_path,
        sha256=sha256,
    )
    db.add(material)
    await db.commit()
    await db.refresh(material)

    # Add signed download URL
    material.download_url = generate_signed_url(material.id)

    return material


@router.get("/{course_id}/materials", response_model=MaterialList)
async def list_materials(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    course_id: int,
    cursor: Optional[str] = None,
    limit: int = Query(default=20, le=100),
) -> MaterialList:
    """List course materials with cursor-based pagination."""
    # Check course exists and user is enrolled
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    if course.owner_id != current_user.id:
        result = await db.execute(
            select(Enrolment).where(
                Enrolment.course_id == course_id,
                Enrolment.user_id == current_user.id,
                Enrolment.status == EnrolmentStatus.ACTIVE,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in course",
            )

    # Build query
    query = select(Material).where(Material.course_id == course_id)
    
    if cursor:
        try:
            cursor_id = int(cursor)
            query = query.where(Material.id < cursor_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor",
            )

    # Get materials
    query = query.order_by(Material.id.desc()).limit(limit + 1)
    result = await db.execute(query)
    materials = result.scalars().all()

    # Check if there are more results
    has_more = len(materials) > limit
    if has_more:
        materials = materials[:-1]

    # Add signed download URLs
    for material in materials:
        material.download_url = generate_signed_url(material.id)

    # Get next cursor
    next_cursor = str(materials[-1].id) if materials and has_more else None

    return MaterialList(
        items=materials,
        next_cursor=next_cursor,
        has_more=has_more
    ) 