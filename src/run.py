import os
import sys
from google.appengine.ext.webapp.util import run_wsgi_app

sys.path.append(os.path.join(os.path.abspath('.'), 'lib'))
import application

if __name__ == '__main__':
    application.app.run()
