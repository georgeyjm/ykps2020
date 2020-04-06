from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache

from instance.secrets import _CONFIG_OBJ


# Initialize flask instances

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(_CONFIG_OBJ)
app.config.from_pyfile('secrets.py')

db = SQLAlchemy()
db.app = app # Necessary for db.create_all()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

cache = Cache(app)

import ykps2020.views
