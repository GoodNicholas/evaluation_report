"""Gradebook

Revision ID: 0003
Revises: 0002
Create Date: 2024-02-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create assignments table
    op.create_table(
        'assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('max_score', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create assignment_student table
    op.create_table(
        'assignment_student',
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('assignment_id', 'student_id')
    )

    # Create gradebook view
    op.execute("""
    CREATE OR REPLACE VIEW v_gradebook AS
    SELECT 
        a.course_id,
        u.id as student_id,
        a.id as assignment_id,
        as2.score
    FROM assignments a
    CROSS JOIN users u
    LEFT JOIN assignment_student as2 ON as2.assignment_id = a.id AND as2.student_id = u.id
    JOIN enrolments e ON e.user_id = u.id AND e.course_id = a.course_id
    WHERE e.status = 'active'
    """)


def downgrade() -> None:
    # Drop gradebook view
    op.execute('DROP VIEW IF EXISTS v_gradebook')

    # Drop assignment_student table
    op.drop_table('assignment_student')

    # Drop assignments table
    op.drop_table('assignments') 