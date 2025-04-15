"""Add admin audit logs table

Revision ID: add_admin_audit_logs_table
Revises: add_game_soft_delete_columns
Create Date: 2025-04-14 20:47:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_admin_audit_logs_table'
down_revision = 'add_game_soft_delete_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Create admin_audit_logs table
    op.create_table('admin_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.Enum('game_delete', 'game_restore', 'match_unapprove', 'match_unsubmit', name='adminactiontype'), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('previous_state', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('new_state', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_admin_audit_target', 'admin_audit_logs', ['target_type', 'target_id'])
    op.create_index('idx_admin_audit_admin', 'admin_audit_logs', ['admin_id'])

def downgrade():
    # Drop admin_audit_logs table and indexes
    op.drop_index('idx_admin_audit_admin', table_name='admin_audit_logs')
    op.drop_index('idx_admin_audit_target', table_name='admin_audit_logs')
    op.drop_table('admin_audit_logs')

    # Drop enum type if exists
    op.execute('DROP TYPE IF EXISTS adminactiontype')