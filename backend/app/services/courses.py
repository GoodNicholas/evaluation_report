from __future__ import annotations

import hashlib
import hmac
import os
import time
import uuid
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.course import Course, Enrolment, EnrolmentStatus
from app.models.material import Material
from app.models.user import User
from app.schemas.course import CourseCreate, CourseUpdate

settings = get_settings()

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

async def create_course(
    db: AsyncSession,
    current_user: User,
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



async def get_course(
    db: AsyncSession,
    current_user: User,
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

async def upload_material(
    db: AsyncSession,
    current_user: User,
    course_id: int,
    file: UploadFile,
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

    # Validate MIME type
    allowed_mime_types = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "image/jpeg",
        "image/png",
    }
    if file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
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

    # Check for duplicate file
    sha256 = hashlib.sha256(content).hexdigest()
    result = await db.execute(
        select(Material).where(
            Material.course_id == course_id,
            Material.sha256 == sha256,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="File already exists",
        )

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
        mime_type=file.content_type,
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

async def list_materials(
    db: AsyncSession,
    current_user: User,
    course_id: int,
    cursor: Optional[str] = None,
    limit: int = 20,
) -> tuple[list[Material], Optional[str], bool]:
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

    return materials, next_cursor, has_more


async def update_course(
    db: AsyncSession,
    current_user: User,
    course_id: int,
    course_in: CourseUpdate,
) -> Course:
    """Update course details."""
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

    for field, value in course_in.model_dump(exclude_unset=True).items():
        setattr(course, field, value)

    await db.commit()
    await db.refresh(course)
    return course
