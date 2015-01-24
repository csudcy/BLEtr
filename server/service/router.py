import datetime
import functools
import json

from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for


def form2kwargs(func):
    @functools.wraps(func)
    def inner():
        # Unfortunately we can't just func(**request.form) as all the values are arrays!

        # So, convert the form to a normal dict
        form = dict(**request.form)

        # Check each arg for single length arrays
        for key in form.iterkeys():
            if not isinstance(form[key], list):
                raise Exception(
                    'Why isnt this argument ({key}) a list?'.format(
                        key=key,
                    )
                )
            if len(form[key]) == 1:
                form[key] = form[key][0]

            # Are we json decoding?
            if isinstance(form[key], basestring):
                if form[key][0] in ('[', '{'):
                    # This might be JSON
                    try:
                        form[key] = json.loads(form[key])
                    except Exception, ex:
                        # Not JSON
                        pass

        # Now we can ** it
        return func(**form)
    return inner

def init(app, db, auth):
    @app.route('/', methods=['GET', 'POST'])
    def splash():
        error = False
        if request.method == 'POST':
            # Login with the request parameters
            success = auth.login(
                request.form['username'],
                request.form['password'],
            )
            error = not success
        if auth.get_current_user() is not None:
            # User is logged in, redirect to the good stuff
            return redirect(url_for('bletr'))
        return render_template(
            'index.html',
            error=error,
        )

    @app.route('/logout/', methods=['GET', 'POST'])
    @auth.authorised
    def logout():
        auth.logout()
        return redirect(url_for('splash'))

    @app.route('/bletr/', methods=['GET'])
    @auth.authorised
    def bletr():
        return render_template(
            'bletr.html',
        )

    @app.route('/clear_events/', methods=['GET', 'POST'])
    @auth.authorised
    def clear_events():
        """
        Quickly clear all events from the database
        """
        if request.method == 'POST':
            if not request.user.is_admin:
                raise Exception('Only admin users can clear events!')

            events = db.session.query(
                db.models.Event
            )
            event_count = events.count()
            events.delete()
            db.session.commit()
            return '+OK REMOVED {event_count} EVENTS'.format(
                event_count=event_count,
            )

        return render_template(
            'clear_events.html',
        )

    @app.route('/report/', methods=['POST'])
    @form2kwargs
    @auth.authorised
    def report(events):
        """
        Receive a report from BLEtr
        """
        # Parse events into the database
        for event in events:
            event_obj = db.models.Event(
                user=request.user,
                seen_at=datetime.datetime.fromtimestamp(event['timestamp']),
                beacon_id=event['id'],
                beacon_distance=event['distance'],
            )
            db.session.add(event_obj)
        db.session.commit()

        # Let the client know what happened
        return '+OK RECEIVED {event_count} EVENTS'.format(
            event_count=len(events)
        )
