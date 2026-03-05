"""
Database Migration for Individual M-Pesa Statement Tables
Adds tables for storing individual client M-Pesa statements and transactions
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_add_mpesa_statement_tables'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Create M-Pesa statement and transaction tables"""
    
    # Create mpesa_statements table
    op.create_table(
        'mpesa_statements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('credit_subject_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_name', sa.String(length=255), nullable=False),
        sa.Column('mobile_number', sa.String(length=20), nullable=False),
        sa.Column('statement_date', sa.DateTime(), nullable=False),
        sa.Column('statement_period', sa.String(length=100), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('upload_date', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['credit_subject_id'], ['credit_subjects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mpesa_statements_id'), 'mpesa_statements', ['id'], unique=False)
    op.create_index(op.f('ix_mpesa_statements_credit_subject_id'), 'mpesa_statements', ['credit_subject_id'], unique=False)
    
    # Create mpesa_transactions table
    op.create_table(
        'mpesa_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('statement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('receipt_no', sa.String(length=50), nullable=False),
        sa.Column('completion_time', sa.DateTime(), nullable=False),
        sa.Column('transaction_type', sa.String(length=100), nullable=False),
        sa.Column('details', sa.Text(), nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('is_paid_in', sa.Boolean(), nullable=False),
        sa.Column('is_paid_out', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['statement_id'], ['mpesa_statements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mpesa_transactions_id'), 'mpesa_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_mpesa_transactions_statement_id'), 'mpesa_transactions', ['statement_id'], unique=False)
    op.create_index(op.f('ix_mpesa_transactions_completion_time'), 'mpesa_transactions', ['completion_time'], unique=False)

def downgrade():
    """Remove M-Pesa statement and transaction tables"""
    
    # Drop mpesa_transactions table
    op.drop_index(op.f('ix_mpesa_transactions_completion_time'), table_name='mpesa_transactions')
    op.drop_index(op.f('ix_mpesa_transactions_statement_id'), table_name='mpesa_transactions')
    op.drop_index(op.f('ix_mpesa_transactions_id'), table_name='mpesa_transactions')
    op.drop_table('mpesa_transactions')
    
    # Drop mpesa_statements table
    op.drop_index(op.f('ix_mpesa_statements_credit_subject_id'), table_name='mpesa_statements')
    op.drop_index(op.f('ix_mpesa_statements_id'), table_name='mpesa_statements')
    op.drop_table('mpesa_statements')
