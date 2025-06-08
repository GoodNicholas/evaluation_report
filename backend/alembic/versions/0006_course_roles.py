"""course roles

Revision ID: 0006
Revises: 0005
Create Date: 2024-02-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0004'
branch_labels = None
depends_on = None

def upgrade():
    # Create enum type for course roles
    op.execute("CREATE TYPE course_role_enum AS ENUM ('owner', 'teacher', 'assistant')")
    
    # Create course_roles table
    op.create_table(
        'course_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', postgresql.ENUM('owner', 'teacher', 'assistant', name='course_role_enum'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique constraint to prevent duplicate roles
    op.create_unique_constraint(
        'uq_course_roles_course_user',
        'course_roles',
        ['course_id', 'user_id']
    )
    
    # Create index for faster lookups
    op.create_index(
        'ix_course_roles_course_user',
        'course_roles',
        ['course_id', 'user_id']
    )
    
    # Migrate existing course owners to course_roles
    op.execute("""
        INSERT INTO course_roles (course_id, user_id, role, created_at, updated_at)
        SELECT id, owner_id, 'owner', created_at, updated_at
        FROM courses
    """)

def downgrade():
    op.drop_index('ix_course_roles_course_user', table_name='course_roles')
    op.drop_constraint('uq_course_roles_course_user', 'course_roles', type_='unique')
    op.drop_table('course_roles')
    op.execute('DROP TYPE course_role_enum') 