"""Add manufacturing_country column to Car table

Revision ID: a14fad792ebd
Revises: 8df93bd4d760
Create Date: 2024-07-24 22:20:54.990498

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a14fad792ebd'
down_revision = '8df93bd4d760'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('car', schema=None) as batch_op:
        batch_op.add_column(sa.Column('manufacturing_country', sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('car', schema=None) as batch_op:
        batch_op.drop_column('manufacturing_country')

    # ### end Alembic commands ###