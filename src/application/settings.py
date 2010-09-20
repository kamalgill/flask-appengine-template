"""
settings.py

Configuration for Flask app

Important: Place your keys in the secret_keys.py module, 
           which will be kept out of version control.

"""


import os
from secret_keys import CSRF_SECRET_KEY, SESSION_KEY


# Auto-set debug mode based on App Engine dev environ
DEBUG_MODE = os.environ['SERVER_SOFTWARE'].startswith('Dev')

DEBUG = DEBUG_MODE

# Set secret keys for CSRF protection
SECRET_KEY = CSRF_SECRET_KEY
CSRF_SESSION_LKEY = SESSION_KEY

CSRF_ENABLED = True

