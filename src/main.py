"""
main.py

Primary App Engine app handler

"""

import sys, os

package_dir = "packages"

# Allow unzipped packages to be imported
# from packages folder
sys.path.insert(0, package_dir)

# Append zip archives to path for zipimport
for filename in os.listdir(package_dir):
    if filename.endswith((".zip", ".egg")):
        sys.path.insert(0, "%s/%s" % (package_dir, filename))

from google.appengine.ext.webapp.util import run_wsgi_app
from application import app


def main():
    run_wsgi_app(app)


# Use App Engine app caching
if __name__ == "__main__":
    main()

