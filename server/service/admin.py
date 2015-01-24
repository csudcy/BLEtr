from flask import session
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from wtforms import ValidationError
import wtforms as wtf


def check_password_fields(f_new, f_confirm, required=False):
    """
    Check if the given password fields match
    """
    if f_new.data or f_confirm.data:
        # A new password has been entered
        if f_new.data != f_confirm.data:
            # Passwords dont match
            f_new.errors.append('Passwords don\'t match')
        else:
            return True
    elif required:
        # This is required (probably a new item), we have to have passwords set
        f_new.errors.append('You must enter a password')

    return False


def init(app, db, auth):
    class AuthenticateModelView(ModelView):
        def is_accessible(self):
            user = auth.get_current_user()
            if user:
                return user.is_admin
            return False

    class UserAdminView(AuthenticateModelView):
        column_list = (
            'username',
            'is_admin',
        )
        form_columns = (
            'username',
            'is_admin',
            'password_new',
            'password_confirm',
        )
        form_extra_fields = {
            'password_new': wtf.PasswordField('Password'),
            'password_confirm': wtf.PasswordField('Password (Confirm)'),
        }

        def on_model_change(self, form, model, is_created):
            # Verify the password
            set_password = check_password_fields(
                form.password_new,
                form.password_confirm,
                required=is_created,
            )
            if set_password:
                model.password = form.password_new.data

            # Continue with the normal validation
            ret = super(UserAdminView, self).on_model_change(form, model, is_created)

            # Check if we added any errors
            if len(form.password_new.errors) > 0:
                raise ValidationError()

            return ret

    class EventView(AuthenticateModelView):
        column_list = (
            'user',
            'seen_at',
            'beacon_id',
            'beacon_distance',
        )
        column_default_sort = 'seen_at'

    admin = Admin(app)
    admin.add_view(UserAdminView(db.models.User, db.session))
    admin.add_view(EventView(db.models.Event, db.session))
