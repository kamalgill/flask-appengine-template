from flask import __version__ as flask_version
from flask_debugtoolbar.panels import DebugPanel

_ = lambda x: x

class VersionDebugPanel(DebugPanel):
    """
    Panel that displays the Flask version.
    """
    name = 'Version'
    has_content = False

    def nav_title(self):
        return _('Versions')

    def nav_subtitle(self):
        return 'Flask %s' % flask_version

    def url(self):
        return ''

    def title(self):
        return _('Versions')

    def content(self):
        return None


