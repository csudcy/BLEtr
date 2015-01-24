"""
Add beacon table and beacon_distance view

Revision ID: 235890a8bc08
Revises: 157fe90914fa
Create Date: 2014-12-28 10:59:55.936000
"""

# revision identifiers, used by Alembic.
revision = '235890a8bc08'
down_revision = '157fe90914fa'

from alembic import op
import sqlalchemy as sa


CREATE_VIEW = """CREATE VIEW beacon_distance AS
SELECT beacon_distances.beacon_id_1,
    beacon_distances.beacon_id_2,
    AVG(beacon_distances.beacon_distance) AS beacon_distance,
    COUNT(*),
    STDDEV(beacon_distances.beacon_distance)
FROM (
    SELECT DISTINCT LEAST(close_beacon_times.beacon_id, event.beacon_id) AS beacon_id_1,
        GREATEST(close_beacon_times.beacon_id, event.beacon_id) AS beacon_id_2,
        event.beacon_distance
    FROM (
        SELECT beacon_id,
            seen_at
        FROM event
        WHERE beacon_distance < 0.1
        GROUP BY beacon_id, seen_at
    ) AS close_beacon_times
    INNER JOIN event ON event.beacon_id != close_beacon_times.beacon_id
        AND ABS(EXTRACT(EPOCH FROM (event.seen_at - close_beacon_times.seen_at))) < 1
) AS beacon_distances
GROUP BY beacon_distances.beacon_id_1, beacon_distances.beacon_id_2
ORDER BY beacon_distances.beacon_id_1, beacon_distances.beacon_id_2
"""

DROP_VIEW = "DROP VIEW beacon_distance"

def upgrade():
    op.create_table('beacon',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('area', sa.Integer(), nullable=True),
        sa.Column('x', sa.Integer(), nullable=True),
        sa.Column('y', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.execute(CREATE_VIEW)


def downgrade():
    op.drop_table('beacon')
    op.execute(DROP_VIEW)
