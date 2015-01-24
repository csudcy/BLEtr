import os

from flask.ext.migrate import MigrateCommand
from flask.ext.script import Manager


def init(app):
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)

    @manager.command
    def production():
        """
        Run the server in production mode
        """
        # Turn off debug on live...
        app.debug = False

        # Upgrade the DB
        from flask.ext.migrate import upgrade
        upgrade()

        # Bind to PORT if defined, otherwise default to 5000.
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)

    return manager
