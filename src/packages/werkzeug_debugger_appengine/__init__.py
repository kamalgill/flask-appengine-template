import os
import sys

from jinja2 import Environment, FileSystemLoader

# Set the template environment.
env = Environment(loader=FileSystemLoader(os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'templates'))))

# Application wrapped by the debugger.
_debugged_app = None


# werkzeug.debug.utils
def get_template(filename):
    return env.get_template(filename)


def render_template(template_filename, **context):
    return get_template(template_filename).render(**context)


def get_debugged_app(app):
    global _debugged_app

    # Wrap app with the debugger.
    if _debugged_app is None:
        from werkzeug import DebuggedApplication
        _debugged_app = DebuggedApplication(app, evalex=True)

    return _debugged_app


# Monkeypatches
# -------------
# werkzeug.debug.console.HTMLStringO
def seek(self, n, mode=0):
    pass


def readline(self):
    if len(self._buffer) == 0:
        return ''
    ret = self._buffer[0]
    del self._buffer[0]
    return ret


# Patch utils first, to avoid loading Werkzeug's template.
sys.modules['werkzeug.debug.utils'] = sys.modules[__name__]


# Apply all other patches.
from werkzeug.debug.console import HTMLStringO
HTMLStringO.seek = seek
HTMLStringO.readline = readline
