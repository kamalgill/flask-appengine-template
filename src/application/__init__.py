"""
Initialize Flask app

"""

from flask import Flask

app = Flask('application')
app.config.from_object('application.settings')

import urls
