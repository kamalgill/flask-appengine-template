"""
main.py

Primary App Engine app handler

"""

import sys, os

package_dir = "packages"

for filename in os.listdir(package_dir):
    if filename.endswith((".zip", ".egg")):
        sys.path.insert(0, "%s/%s" % (package_dir, filename))

from google.appengine.ext.webapp.util import run_wsgi_app
from application import app

run_wsgi_app(app)
