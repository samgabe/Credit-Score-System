"""Mark current database state as complete

Revision ID: 002_mark_current_state
Revises: 001_initial_migration
Create Date: 2026-03-06 14:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_mark_current_state'
down_revision = '001_initial_migration'
branch_labels = None
depends_on = None


def upgrade():
    # All database changes are already applied
    # This migration just marks the current state
    pass


def downgrade():
    # Reverse to initial state
    pass
