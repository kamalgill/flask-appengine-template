"""
main.py

Primary App Engine app handler

"""

from google.appengine.ext.webapp.util import run_wsgi_app
from application import app

run_wsgi_app(app)
