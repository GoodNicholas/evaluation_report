from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MaterialBase(BaseModel):
    """Base material schema."""

    filename: str
    mime_type: str
    size: int


class MaterialCreate(MaterialBase):
    """Material creation schema."""

    pass


class Material(MaterialBase):
    """Material schema."""

    id: int
    course_id: int
    uploader_id: int
    stored_path: str
    sha256: str
    created_at: datetime
    updated_at: datetime
    download_url: str | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True 