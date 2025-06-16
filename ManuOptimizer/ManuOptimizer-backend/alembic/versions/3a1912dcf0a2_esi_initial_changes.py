"""esi initial changes

Revision ID: 3a1912dcf0a2
Revises: 7859b1f6fda2
Create Date: 2025-06-10 13:25:49.857064

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a1912dcf0a2'
down_revision = '7859b1f6fda2'
branch_labels = None
depends_on = None


def upgrade():
    jita_region_id = 10000002

    # Create new tables 'region' and 'station' (auto generated Alembic code)
    op.create_table(
        'region',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('region_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('region_id')
    )

    op.create_table(
        'station',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('station_id', sa.Integer(), nullable=False),
        sa.Column('region_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('station_id')
    )

    # Add columns to blueprint table, initially allow null for region_id
    with op.batch_alter_table('blueprint', schema=None) as batch_op:
        batch_op.add_column(sa.Column('region_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('station_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('use_region_orders', sa.Boolean(), nullable=False))

    # Update existing rows to set region_id = Jita region ID
    op.execute(f'UPDATE blueprint SET region_id = {jita_region_id} WHERE region_id IS NULL')

    # Alter the region_id column to be NOT NULL now that all rows have values
    with op.batch_alter_table('blueprint', schema=None) as batch_op:
        batch_op.alter_column('region_id', nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # Remove columns from blueprint
    with op.batch_alter_table('blueprint', schema=None) as batch_op:
        batch_op.drop_column('use_region_orders')
        batch_op.drop_column('station_id')
        batch_op.drop_column('region_id')

    # Drop 'station' table
    op.drop_table('station')

    # Drop 'region' table
    op.drop_table('region')
