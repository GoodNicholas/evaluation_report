from __future__ import annotations

from typing import Annotated, AsyncGenerator, Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.security import verify_password
from app.db.session import get_db, SessionLocal
from app.models.user import User
from app.schemas.user import TokenPayload
from app import crud, models, schemas
from app.models.course_role import CourseRoleEnum

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Get current user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        token_data = TokenPayload(**payload)
    except JWTError:
        raise credentials_exception
    if token_data.sub is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(token_data.sub)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return user

def require_role(*allowed: str):
    """Require role decorator."""

    async def guard(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if not any(r.name in allowed for r in user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return user

    return guard

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> models.User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = crud.user.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user

def require_course_role(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    course_id: int = None,
    required_role: CourseRoleEnum = None,
) -> models.CourseRole:
    """
    Dependency to check if the current user has the required role in a course.
    Returns the course role if the user has the required role or higher.
    """
    if not course_id or not required_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course ID and required role must be provided",
        )

    # Get the user's role in the course
    course_role = crud.course_role.get_by_course_and_user(
        db, course_id=course_id, user_id=current_user.id
    )

    if not course_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have any role in this course",
        )

    # Define role hierarchy
    role_hierarchy = {
        CourseRoleEnum.OWNER: 3,
        CourseRoleEnum.TEACHER: 2,
        CourseRoleEnum.ASSISTANT: 1,
    }

    # Check if user's role is sufficient
    if role_hierarchy[course_role.role] < role_hierarchy[required_role]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User must have {required_role} role or higher",
        )

    return course_role 