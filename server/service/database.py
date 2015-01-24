import os

from flask.ext.migrate import Migrate
from flask.ext.sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt


if 'DATABASE_URL' not in os.environ:
    # Looks like we're running locally
    os.environ['DATABASE_URL'] = 'postgres://postgres:postgres@localhost:5432/bletr'


def init(app):
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)

    class Models(object):
        pass
    db.models = Models()

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        is_admin = db.Column(db.Boolean(), nullable=False, default=False)
        username = db.Column(db.String(100), nullable=False)
        password_hashed = db.Column(db.String(200), nullable=False)

        def __unicode__(self):
            return 'User: {username} ({id})'.format(
                username=self.username,
                id=self.id,
            )
        __str__ = __unicode__
        __repr__ = __unicode__

        def set_password(self, password):
            self.password_hashed = sha256_crypt.encrypt(password)

        def verify_password(self, password):
            return sha256_crypt.verify(password, self.password_hashed)

        @property
        def password(self):
            raise Exception('You cannot get the password!')
        @password.setter
        def password(self, value):
            self.password_hashed = sha256_crypt.encrypt(value)

    db.models.User = User


    class Event(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(
            db.Integer,
            db.ForeignKey('user.id', onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        )
        user = db.relationship('User', backref='events')

        seen_at = db.Column(db.DateTime(), nullable=False)
        beacon_id = db.Column(db.String(100), nullable=False)
        beacon_distance = db.Column(db.Float(), nullable=False)

        def __unicode__(self):
            return 'Event: {seen_at} : {beacon_id} : {beacon_distance}'.format(
                seen_at=self.seen_at.strftime('%d/%m/%Y %H:%M:%S'),
                beacon_id=self.beacon_id,
                beacon_distance=self.beacon_distance,
            )
        __str__ = __unicode__
        __repr__ = __unicode__

    db.models.Event = Event


    class Beacon(db.Model):
        id = db.Column(db.String(100), primary_key=True)
        area = db.Column(db.Integer)
        connected_count = db.Column(db.Integer)
        x = db.Column(db.Float)
        y = db.Column(db.Float)

        def __unicode__(self):
            return 'Beacon: {id} in area {area} @ ({x}, {y}) connected with {connected_count} other beacons'.format(
                id=self.id,
                area=self.area,
                connected_count=self.connected_count,
                x=self.x,
                y=self.y,
            )
        __str__ = __unicode__
        __repr__ = __unicode__

    db.models.Beacon = Beacon


    class BeaconDistance(db.Model):
        # TODO: Work out how to make this readonly!
        beacon_id_1 = db.Column(db.String(100), primary_key=True)
        beacon_id_2 = db.Column(db.String(100), primary_key=True)
        beacon_distance = db.Column(db.Float, nullable=False)
        count = db.Column(db.Integer, nullable=False)
        stddev = db.Column(db.Float, nullable=False)

        def __unicode__(self):
            return 'BeaconDistance: {beacon_id_1} to {beacon_id_2} is {beacon_distance}m (based on {count} events with a std dev of {stddev}m)'.format(
                beacon_id_1=self.beacon_id_1,
                beacon_id_2=self.beacon_id_2,
                beacon_distance=self.beacon_distance,
                count=self.count,
                stddev=self.stddev,
            )
        __str__ = __unicode__
        __repr__ = __unicode__

    db.models.BeaconDistance = BeaconDistance


    class EventTimerange(db.Model):
        # TODO: Work out how to make this readonly!
        rn = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(
            db.Integer,
            db.ForeignKey('user.id', onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        )
        user = db.relationship('User', backref='event_timeranges')

        start_time = db.Column(db.DateTime(), nullable=False)
        end_time = db.Column(db.DateTime(), nullable=False)

        def __unicode__(self):
            return '<EventTimerange: {start_time} to {end_time}>'.format(
                start_time=self.start_time,
                end_time=self.end_time,
            )
        __str__ = __unicode__
        __repr__ = __unicode__

    db.models.EventTimerange = EventTimerange

    return db
