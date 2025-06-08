from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MaterialBase(BaseModel):
    """Base material schema."""

    filename: str
    mime_type: str
    size: int
    sha256: str


class MaterialCreate(MaterialBase):
    """Material creation schema."""

    pass


class Material(MaterialBase):
    """Material schema."""

    id: int
    course_id: int
    uploader_id: int
    stored_path: str
    download_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class MaterialList(BaseModel):
    """Material list with pagination."""
    items: list[Material]
    next_cursor: Optional[str] = None
    has_more: bool = False 