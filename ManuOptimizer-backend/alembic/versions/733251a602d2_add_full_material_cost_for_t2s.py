"""Add full material cost for t2s

Revision ID: 733251a602d2
Revises: c36fa1db0bea
Create Date: 2025-05-24 16:25:33.228698

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '733251a602d2'
down_revision = 'c36fa1db0bea'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('blueprint_t2', schema=None) as batch_op:
        batch_op.add_column(sa.Column('full_material_cost', sa.Float(), server_default='0', nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('blueprint_t2', schema=None) as batch_op:
        batch_op.drop_column('full_material_cost')

    # ### end Alembic commands ###
