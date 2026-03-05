"""add_credit_subject_id_to_credit_scores

Revision ID: e1a2b3c4d5e6
Revises: d96673d77997
Create Date: 2026-03-05 12:02:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1a2b3c4d5e6'
down_revision = 'd96673d77997'
branch_labels = None
depends_on = None


def upgrade():
    # Add credit_subject_id column to credit_scores table
    op.add_column('credit_scores', sa.Column('credit_subject_id', sa.UUID(), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'credit_scores_credit_subject_id_fkey',
        'credit_scores', 'credit_subjects',
        ['credit_subject_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Create index
    op.create_index('ix_credit_scores_credit_subject_id', 'credit_scores', ['credit_subject_id'])


def downgrade():
    # Drop index
    op.drop_index('ix_credit_scores_credit_subject_id', table_name='credit_scores')
    
    # Drop foreign key constraint
    op.drop_constraint('credit_scores_credit_subject_id_fkey', 'credit_scores', type_='foreignkey')
    
    # Drop column
    op.drop_column('credit_scores', 'credit_subject_id')
