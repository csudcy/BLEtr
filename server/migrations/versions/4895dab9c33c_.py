"""
Add event_timerange view

Revision ID: 4895dab9c33c
Revises: 533cfaf2a3ec
Create Date: 2014-12-31 11:27:26.406000
"""

# revision identifiers, used by Alembic.
revision = '4895dab9c33c'
down_revision = '533cfaf2a3ec'

from alembic import op
import sqlalchemy as sa


CREATE_VIEW = """CREATE VIEW event_timerange AS
WITH converted AS (
    SELECT ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY seen_at) AS rn,
        user_id,
        CAST(EXTRACT(EPOCH FROM seen_at) AS INTEGER) AS seconds
    FROM event
),
gaps AS (
    SELECT ROW_NUMBER() OVER (ORDER BY dd.c1_seconds) AS rn,
        dd.user_id,
        dd.c1_seconds,
        dd.c2_seconds
    FROM (
        SELECT c1.rn AS c1_rn,
            c1.user_id as user_id,
            c1.seconds AS c1_seconds,
            c2.seconds AS c2_seconds,
            c2.seconds - c1.seconds AS diff
        FROM converted AS c1
        LEFT JOIN converted AS c2 ON c1.rn + 1 = c2.rn
            AND c1.user_id = c2.user_id
    ) AS dd
    WHERE dd.c1_rn = 1
        OR dd.diff IS NULL
        OR dd.diff > 60
)
SELECT g1.rn,
    g1.user_id,
    TO_TIMESTAMP(g1.c2_seconds) AS start_time,
    TO_TIMESTAMP(g2.c1_seconds) AS end_time
FROM gaps AS g1
INNER JOIN gaps AS g2 ON g1.rn + 1 = g2.rn
    AND g1.user_id = g2.user_id
"""

DROP_VIEW = "DROP VIEW event_timerange"

def upgrade():
    op.execute(CREATE_VIEW)


def downgrade():
    op.execute(DROP_VIEW)
