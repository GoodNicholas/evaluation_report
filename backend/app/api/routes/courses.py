from __future__ import annotations

import hashlib
import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
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
from app.schemas.material import Material as MaterialSchema

settings = get_settings()
router = APIRouter()


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

    # Validate file
    if file.size > 20 * 1024 * 1024:  # 20 MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large",
        )

    # Read file content
    content = await file.read()
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
        size=len(content),
        stored_path=stored_path,
        sha256=sha256,
    )
    db.add(material)
    await db.commit()
    await db.refresh(material)

    return material


@router.get("/{course_id}/materials", response_model=list[MaterialSchema])
async def list_materials(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    course_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Material]:
    """List course materials."""
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

    # Get materials
    result = await db.execute(
        select(Material)
        .where(Material.course_id == course_id)
        .offset(skip)
        .limit(limit)
    )
    materials = result.scalars().all()

    # Add download URLs
    for material in materials:
        material.download_url = f"/materials/{material.id}/download"

    return materials 