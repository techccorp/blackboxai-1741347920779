#--------------------------------------------------------#
#                  app/extensions.py                     #
#--------------------------------------------------------#

from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

mongo = PyMongo()
bcrypt = Bcrypt()
csrf = CSRFProtect()

def create_indexes(app):
    with app.app_context():
        mongo.db.business_users.create_index([
            ('shifts.date', 1),
            ('company_id', 1),
            ('venue_id', 1)
        ])
