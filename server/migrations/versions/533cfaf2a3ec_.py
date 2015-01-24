"""
Add beacon.connected_count, make beacon.x and y floats

Revision ID: 533cfaf2a3ec
Revises: 235890a8bc08
Create Date: 2014-12-29 14:35:10.769000
"""

# revision identifiers, used by Alembic.
revision = '533cfaf2a3ec'
down_revision = '235890a8bc08'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'beacon',
        sa.Column('connected_count', sa.Integer(), nullable=True)
    )
    op.alter_column(
        'beacon',
        'x',
        type_=sa.Float(),
    )
    op.alter_column(
        'beacon',
        'y',
        type_=sa.Float(),
    )


def downgrade():
    op.drop_column(u'beacon', 'connected_count')
    op.alter_column(
        'beacon',
        'x',
        type_=sa.Integer(),
    )
    op.alter_column(
        'beacon',
        'y',
        type_=sa.Integer(),
    )
