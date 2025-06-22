"""esi initial changes

Revision ID: a2a58868ee8f
Revises: 3a1912dcf0a2
Create Date: 2025-06-10 13:32:10.966045

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2a58868ee8f'
down_revision = '3a1912dcf0a2'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    result = conn.execute(sa.text("PRAGMA table_info(blueprint)"))
    columns = [row[1] for row in result]

    if 'region_id' not in columns:
        op.add_column('blueprint', sa.Column('region_id', sa.Integer(), nullable=True, server_default='10000002'))

    if 'station_id' not in columns:
        op.add_column('blueprint', sa.Column('station_id', sa.Integer(), nullable=True))

    if 'use_region_orders' not in columns:
        op.add_column('blueprint', sa.Column('use_region_orders', sa.Boolean(), nullable=False, server_default=sa.false()))

    # Use batch mode to safely alter nullable on SQLite
    with op.batch_alter_table('blueprint') as batch_op:
        batch_op.alter_column('region_id', nullable=False)



def downgrade():
    conn = op.get_bind()
    result = conn.execute(sa.text("PRAGMA table_info(blueprint)"))
    columns = [row['name'] for row in result]

    if 'use_region_orders' in columns:
        op.drop_column('blueprint', 'use_region_orders')

    if 'station_id' in columns:
        op.drop_column('blueprint', 'station_id')

    if 'region_id' in columns:
        op.drop_column('blueprint', 'region_id')