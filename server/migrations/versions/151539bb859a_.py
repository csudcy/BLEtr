"""
Initial DB creation

Revision ID: 151539bb859a
Revises: None
Create Date: 2014-12-24 22:06:21.830000
"""

# revision identifiers, used by Alembic.
revision = '151539bb859a'
down_revision = None

from alembic import op
from flask_sqlalchemy import _SessionSignalEvents
from passlib.hash import sha256_crypt
from sqlalchemy import event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as BaseSession, relationship
import sqlalchemy as sa

Session = sessionmaker()

event.remove(BaseSession, 'before_commit', _SessionSignalEvents.session_signal_before_commit)
event.remove(BaseSession, 'after_commit', _SessionSignalEvents.session_signal_after_commit)
event.remove(BaseSession, 'after_rollback', _SessionSignalEvents.session_signal_after_rollback)

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = sa.Column(sa.Integer, primary_key=True)
    is_admin = sa.Column(sa.Boolean(), nullable=False, default=False)
    username = sa.Column(sa.String(100), nullable=False)
    password_hashed = sa.Column(sa.String(200), nullable=False)


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_hashed', sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('seen_at', sa.Date(), nullable=False),
        sa.Column('beacon_id', sa.String(length=100), nullable=False),
        sa.Column('beacon_distance', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add the admin user
    bind = op.get_bind()
    session = Session(bind=bind)
    admin_user = User(
        is_admin=True,
        username='admin',
        password_hashed=sha256_crypt.encrypt('password'),
    )
    session.add(admin_user)
    session.commit()


def downgrade():
    op.drop_table('event')
    op.drop_table('user')
