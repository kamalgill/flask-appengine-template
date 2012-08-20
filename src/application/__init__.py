"""
Initialize Flask app

"""

from flask import Flask
from flaskext.gae_mini_profiler import GAEMiniProfiler


app = Flask('application')
app.config.from_object('application.settings')

# Enable profiler (enabled in non-production environ only)
GAEMiniProfiler(app)

# Pull in URL dispatch routes
import urls
