import logging

from flask import Flask
from flask.ext.heroku import Heroku

from service import admin
from service import cli
from service import database
from service import mlat
from service import router
from service.auth import Auth

##################################################
#                    Logging
##################################################

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

for disabled_logger in ('pyexchange', ):
    dl = logging.getLogger(disabled_logger)
    dl.propagate = False

##################################################
#                    Setup
##################################################

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'This is the secret key for BLEtr.'
heroku = Heroku(app)

##################################################
#                    Services
##################################################
db = database.init(app)
auth = Auth(db)
admin.init(app, db, auth)
router.init(app, db, auth)
manager = cli.init(app)

##################################################
#                    Main
##################################################

if __name__ == '__main__':
    # mlat.calc_all(db)
    mlat.test_get_position(db)
    manager.run()
