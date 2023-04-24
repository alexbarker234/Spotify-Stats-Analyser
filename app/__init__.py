import os
import logging
from config import Config
from logging.handlers import RotatingFileHandler
from datetime import date

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_dropzone import Dropzone

from flask_assets import Environment, Bundle
import glob

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
assets = Environment(app)
dropzone = Dropzone(app)

# bundles
css_files = glob.glob("app/static/css/*.css")
css_files = [i.replace('app/static/','') for i in css_files] # remove path as flask_assets works from static directory
css = Bundle(*css_files, output='gen/packed.css')
assets.register('css_all', css)


js_files = glob.glob("app/static/js/*.js")
js_files = [i.replace('app/static/','') for i in js_files] # remove path as flask_assets works from static directory
css = Bundle(*js_files, output='gen/packed.js')
assets.register('js_all', css)
# could potentially include jQuery & bootstrap.js in here

# logging
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/flasktest_{}.log'.format(date.today()))
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('flasktest startup')

from app import routes, models, errors