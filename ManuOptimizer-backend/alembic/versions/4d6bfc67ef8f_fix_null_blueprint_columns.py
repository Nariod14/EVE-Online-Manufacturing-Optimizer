from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_blueprint_columns'
down_revision = '3a1912dcf0a2'
branch_labels = None
depends_on = None


def upgrade():
    jita_region_id = 10000002
    jita_station_id = 60003760

    # Fill in missing values in case previous migration didn't
    op.execute(f'''
        UPDATE blueprint
        SET
            region_id = {jita_region_id},
            station_id = {jita_station_id},
            use_region_orders = 1
        WHERE region_id IS NULL OR station_id IS NULL OR use_region_orders IS NULL
    ''')

    # Ensure columns are not nullable (just in case)
    with op.batch_alter_table('blueprint', schema=None) as batch_op:
        batch_op.alter_column('region_id', nullable=False)
        batch_op.alter_column('station_id', nullable=False)
        batch_op.alter_column('use_region_orders', nullable=False)


def downgrade():
    # Be cautious with downgrades that might unset critical data
    with op.batch_alter_table('blueprint', schema=None) as batch_op:
        batch_op.alter_column('region_id', nullable=True)
        batch_op.alter_column('station_id', nullable=True)
        batch_op.alter_column('use_region_orders', nullable=True)
