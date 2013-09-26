"""
App Engine config

"""


def gae_mini_profiler_should_profile_production():
    """Uncomment the first two lines to enable GAE Mini Profiler on production for admin accounts"""
    # from google.appengine.api import users
    # return users.is_current_user_admin()
    return False


def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app
