"""
Initialize Flask app

"""
from flask import Flask
import os

from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.debug import DebuggedApplication

app = Flask('application')

if os.getenv('FLASK_CONF') == 'DEV':
	#development settings not to be used in production
    app.config.from_object('application.settings.Development')
	# Flask-DebugToolbar (only enabled when DEBUG=True)
    toolbar = DebugToolbarExtension(app)
    # Werkzeug Debugger - enabled by default in new versions of Flask 
    #if you set debug to true, right?
    # app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

elif os.getenv('FLASK_CONF') == 'TEST':
    app.config.from_object('application.settings.Testing')

else:
    app.config.from_object('application.settings.Production')

# Remember to set SERVER_SOFTWARE environment variable
# to value "Devel" to use this
from gae_mini_profiler import profiler, templatetags 

@app.context_processor
def inject_profiler():
	    return dict(profiler_includes=templatetags.profiler_includes())

app.wsgi_app = profiler.ProfilerWSGIMiddleware(app.wsgi_app)

# Enable jinja2 loop controls extension
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

# Pull in URL dispatch routes
import urls