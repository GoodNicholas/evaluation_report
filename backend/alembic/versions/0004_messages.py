"""Messages

Revision ID: 0004
Revises: 0003
Create Date: 2024-02-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create dialogs table
    op.create_table(
        "dialogs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["teacher_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create messages table
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dialog_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(
            ["dialog_id"],
            ["dialogs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add indexes
    op.create_index(
        "ix_dialogs_course_teacher_student",
        "dialogs",
        ["course_id", "teacher_id", "student_id"],
        unique=True,
    )
    op.create_index(
        "ix_messages_dialog_created",
        "messages",
        ["dialog_id", "created_at"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_messages_dialog_created")
    op.drop_index("ix_dialogs_course_teacher_student")

    # Drop tables
    op.drop_table("messages")
    op.drop_table("dialogs") 