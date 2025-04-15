"""merge admin and deck versioning branches

Revision ID: caebb3d6cb25
Revises: add_admin_and_password_reset, c92f19bc96aa
Create Date: 2025-04-10 21:11:38.261063

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'caebb3d6cb25'
down_revision = ('add_admin_and_password_reset', 'c92f19bc96aa')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
