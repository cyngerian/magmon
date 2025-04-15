"""Add game soft delete columns

Revision ID: add_game_soft_delete_columns
Revises: caebb3d6cb25
Create Date: 2025-04-14 20:44:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_game_soft_delete_columns'
down_revision = 'caebb3d6cb25'
branch_labels = None
depends_on = None

def upgrade():
    # Add soft delete and admin action columns to games table
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('deleted_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('last_admin_action', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('last_admin_action_at', sa.DateTime(), nullable=True))
        batch_op.create_foreign_key('fk_games_deleted_by_id_users', 'users', ['deleted_by_id'], ['id'])

def downgrade():
    # Remove columns from games table
    with op.batch_alter_table('games', schema=None) as batch_op:
        batch_op.drop_constraint('fk_games_deleted_by_id_users', type_='foreignkey')
        batch_op.drop_column('last_admin_action_at')
        batch_op.drop_column('last_admin_action')
        batch_op.drop_column('deleted_by_id')
        batch_op.drop_column('deleted_at')