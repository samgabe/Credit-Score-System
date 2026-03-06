"""Initial migration - represent current database state

Revision ID: 001_initial_migration
Revises: 
Create Date: 2026-03-06 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # This migration represents the current state of the database
    # All tables already exist, so we just need to ensure they're properly tracked
    # The alembic_version table entry will be created automatically
    pass


def downgrade():
    # Remove alembic version entry
    op.execute("DELETE FROM alembic_version WHERE version_num = '001_initial_migration'")
