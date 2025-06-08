from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.course import Course, Enrolment, EnrolmentStatus
from app.models.user import User
from app.schemas.gradebook import Gradebook, GradebookCell, GradebookUpdate


async def get_gradebook(
    db: AsyncSession,
    current_user: User,
    course_id: int,
) -> Gradebook:
    """Get gradebook for a course."""
    # Check course exists and user has access
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    # Get assignments
    result = await db.execute(
        select(Assignment).where(Assignment.course_id == course_id)
    )
    assignments = result.scalars().all()

    # Get gradebook data
    query = text("""
        SELECT 
            u.id as student_id,
            u.first_name || ' ' || u.last_name as student_name,
            a.id as assignment_id,
            g.score
        FROM v_gradebook g
        JOIN users u ON u.id = g.student_id
        JOIN assignments a ON a.id = g.assignment_id
        WHERE g.course_id = :course_id
        ORDER BY u.id, a.id
    """)
    result = await db.execute(query, {"course_id": course_id})
    rows = result.all()

    # Format data
    student_scores: dict[int, dict[int, Optional[int]]] = {}
    for row in rows:
        if row.student_id not in student_scores:
            student_scores[row.student_id] = {
                "name": row.student_name,
                "scores": {},
            }
        student_scores[row.student_id]["scores"][row.assignment_id] = row.score

    # Filter rows based on user role
    if not any(r.name == "teacher" for r in current_user.roles):
        # Student can only see their own row
        if current_user.id not in student_scores:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in course",
            )
        student_scores = {current_user.id: student_scores[current_user.id]}

    # Format response
    gradebook_rows = [
        {
            "student_id": student_id,
            "student_name": data["name"],
            "scores": data["scores"],
        }
        for student_id, data in student_scores.items()
    ]

    return Gradebook(
        assignments=assignments,
        rows=gradebook_rows,
    )


async def update_gradebook(
    db: AsyncSession,
    current_user: User,
    course_id: int,
    update: GradebookUpdate,
) -> None:
    """Update gradebook scores."""
    # Check course exists and user is teacher
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    if not any(r.name == "teacher" for r in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Validate all students are enrolled
    student_ids = {cell.student_id for cell in update.updates}
    result = await db.execute(
        select(Enrolment).where(
            Enrolment.course_id == course_id,
            Enrolment.user_id.in_(student_ids),
            Enrolment.status == EnrolmentStatus.ACTIVE,
        )
    )
    enrolled_students = {e.user_id for e in result.scalars().all()}
    if not enrolled_students.issuperset(student_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some students are not enrolled in the course",
        )

    # Validate all assignments belong to the course
    assignment_ids = {cell.assignment_id for cell in update.updates}
    result = await db.execute(
        select(Assignment).where(
            Assignment.course_id == course_id,
            Assignment.id.in_(assignment_ids),
        )
    )
    course_assignments = {a.id for a in result.scalars().all()}
    if not course_assignments.issuperset(assignment_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some assignments do not belong to the course",
        )

    # Update scores
    for cell in update.updates:
        query = text("""
            INSERT INTO assignment_student (assignment_id, student_id, score)
            VALUES (:assignment_id, :student_id, :score)
            ON CONFLICT (assignment_id, student_id)
            DO UPDATE SET score = :score
        """)
        await db.execute(
            query,
            {
                "assignment_id": cell.assignment_id,
                "student_id": cell.student_id,
                "score": cell.score,
            },
        )

    await db.commit() 