"""add admin and password reset fields

Revision ID: add_admin_and_password_reset
Revises: 7800133a9ad6
Create Date: 2025-04-10 21:04:20.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_admin_and_password_reset'
down_revision = '7800133a9ad6'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('temp_password_hash', sa.String(128), nullable=True))
    op.add_column('users', sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('temp_password_expires_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))

    # Create index on is_admin for faster admin checks
    op.create_index(op.f('ix_users_is_admin'), 'users', ['is_admin'], unique=False)

    # Set initial admin user (you'll need to update this with the correct user ID)
    op.execute("UPDATE users SET is_admin = true WHERE id = 1")

def downgrade():
    # Remove columns from users table
    op.drop_index(op.f('ix_users_is_admin'), table_name='users')
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'temp_password_expires_at')
    op.drop_column('users', 'must_change_password')
    op.drop_column('users', 'temp_password_hash')
    op.drop_column('users', 'is_admin')