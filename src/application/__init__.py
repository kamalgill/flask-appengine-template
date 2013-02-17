"""
Initialize Flask app

"""
from flask import Flask

from flask_debugtoolbar import DebugToolbarExtension
from gae_mini_profiler import profiler, templatetags


app = Flask('application')
app.config.from_object('application.settings')

# Enable jinja2 loop controls extension
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

@app.context_processor
def inject_profiler():
    return dict(profiler_includes=templatetags.profiler_includes())

# Pull in URL dispatch routes
import urls

# Flask-DebugToolbar (only enabled when DEBUG=True)
toolbar = DebugToolbarExtension(app)

# GAE Mini Profiler (only enabled on dev server)
app = profiler.ProfilerWSGIMiddleware(app)

