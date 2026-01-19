"""update_user_model_with_enhanced_fields

Revision ID: 5c616275cc70
Revises: be67793cedd3
Create Date: 2026-01-16 15:50:08.535488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c616275cc70'
down_revision: Union[str, None] = 'be67793cedd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Update users table to add enhanced profile fields:
    - Rename 'name' to 'fullname'
    - Rename 'phone' to 'phone_number'
    - Add 'national_id' field with unique constraint (as INTEGER)
    - Make 'email' nullable for backward compatibility
    """
    # Add new columns (initially nullable to allow migration of existing data)
    op.add_column('users', sa.Column('fullname', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('national_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))
    
    # Copy data from old columns to new columns
    op.execute('UPDATE users SET fullname = name')
    op.execute('UPDATE users SET phone_number = phone')
    
    # Make email nullable for backward compatibility
    op.alter_column('users', 'email', nullable=True)
    
    # Drop the unique constraint on email if it exists
    connection = op.get_bind()
    result = connection.execute(sa.text(
        "SELECT constraint_name FROM information_schema.table_constraints "
        "WHERE table_name = 'users' AND constraint_name = 'users_email_key'"
    ))
    if result.fetchone():
        op.drop_constraint('users_email_key', 'users', type_='unique')
    
    # Now make the new columns non-nullable (except national_id which stays nullable for migration)
    op.alter_column('users', 'fullname', nullable=False)
    op.alter_column('users', 'phone_number', nullable=False)
    
    # Drop old columns
    op.drop_column('users', 'name')
    op.drop_column('users', 'phone')
    
    # Add unique constraint and index on national_id
    op.create_unique_constraint('users_national_id_key', 'users', ['national_id'])
    op.create_index(op.f('ix_users_national_id'), 'users', ['national_id'], unique=False)


def downgrade() -> None:
    """
    Revert users table changes:
    - Rename 'fullname' back to 'name'
    - Rename 'phone_number' back to 'phone'
    - Remove 'national_id' field
    - Make 'email' non-nullable again
    """
    # Drop index and constraint on national_id
    op.drop_index(op.f('ix_users_national_id'), table_name='users')
    op.drop_constraint('users_national_id_key', 'users', type_='unique')
    
    # Add old columns back
    op.add_column('users', sa.Column('name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True))
    
    # Copy data back
    op.execute('UPDATE users SET name = fullname')
    op.execute('UPDATE users SET phone = phone_number')
    
    # Make old columns non-nullable
    op.alter_column('users', 'name', nullable=False)
    op.alter_column('users', 'phone', nullable=False)
    
    # Drop new columns
    op.drop_column('users', 'phone_number')
    op.drop_column('users', 'national_id')
    op.drop_column('users', 'fullname')
    
    # Make email non-nullable and add unique constraint back
    op.alter_column('users', 'email', nullable=False)
    op.create_unique_constraint('users_email_key', 'users', ['email'])

