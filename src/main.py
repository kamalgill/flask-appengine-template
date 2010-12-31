"""
main.py

Primary App Engine app handler

"""

import sys, os
for filename in os.listdir("packages"):
    if filename.endswith(".zip"):
        sys.path.insert(0, "packages/%s" % filename)

from google.appengine.ext.webapp.util import run_wsgi_app
from application import app

run_wsgi_app(app)
