from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import profiler

application = webapp.WSGIApplication([
    ("/gae_mini_profiler/request/log", profiler.RequestLogHandler),
    ("/gae_mini_profiler/request", profiler.RequestStatsHandler),
    ("/gae_mini_profiler/shared", profiler.SharedStatsHandler),
])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
