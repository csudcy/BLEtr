"""
Change event.seen_at from date to datetime

Revision ID: 157fe90914fa
Revises: 151539bb859a
Create Date: 2014-12-27 12:40:39.633000
"""

# revision identifiers, used by Alembic.
revision = '157fe90914fa'
down_revision = '151539bb859a'

from alembic import op
import sqlalchemy as sa

metadata = sa.MetaData()

def upgrade():
    op.alter_column(
        'event',
        'seen_at',
        type_=sa.DateTime,
    )

def downgrade():
    op.alter_column(
        'event',
        'seen_at',
        type_=sa.Date,
    )
