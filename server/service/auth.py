import functools

from flask import redirect
from flask import request
from flask import session
from flask import url_for
from sqlalchemy.orm.exc import NoResultFound

class Auth(object):
    def __init__(self, db):
        self.db = db

    def login(self, username, password):
        """
        Login the given user
        """
        # Is this an existing user?
        try:
            user = self.db.session.query(
                self.db.models.User
            ).filter(
                self.db.models.User.username == username
            ).one()
        except NoResultFound, ex:
            return False

        # Check the password matches
        if not user.verify_password(password):
            return False

        # Setup the session
        session.permanent = True
        session['user_id'] = user.id

        # We really are logged in!
        return True

    def logout(self):
        """
        Remove the current session
        """
        session.clear()

    def get_current_user(self):
        # Check there is a user in the session
        if session.get('user_id', None) is None:
            return None

        # Check the user is still valid
        try:
            user = self.db.session.query(
                self.db.models.User
            ).filter(
                self.db.models.User.id == session['user_id']
            ).one()
        except NoResultFound, ex:
            # User no longer exists in the database, they need to login again
            return None

        # Everything pass
        return user

    def authorised(self, func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            # Do we want to login right now?
            if 'login_username' in kwargs or 'login_password' in kwargs:
                login_username = kwargs.pop('login_username')
                login_password = kwargs.pop('login_password')
                self.login(login_username, login_password)

            # Check if we have a logged in user
            current_user = self.get_current_user()
            if current_user is None:
                # Bad user, you're not logged in!
                return redirect(url_for('splash'))

            # Add the user on the request
            request.user = current_user

            # Run the original function
            return func(*args, **kwargs)
        return inner
