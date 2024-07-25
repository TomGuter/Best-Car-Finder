"""Fix migration after manual table deletion

Revision ID: aafd60fe24d9
Revises: 4d8ace222238
Create Date: 2024-07-25 11:05:30.136426

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aafd60fe24d9'
down_revision = '4d8ace222238'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
