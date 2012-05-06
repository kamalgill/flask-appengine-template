"""
    gae_mini_profiler
    ~~~~~~~~~~~~~~~~~

    :copyright: (c) 2011, Ben Kamens
    :url: https://github.com/kamens/gae_mini_profiler
    :license: MIT, see LICENSE for more details
"""


import datetime
import logging
import os
import pickle
import simplejson
import StringIO
import sys
from types import GeneratorType
import zlib

from google.appengine.ext.webapp import RequestHandler
from google.appengine.api import memcache

# request_id is a per-request identifier accessed by a couple other pieces of gae_mini_profiler
request_id = None


class RequestStatsHandler(RequestHandler):

    def get(self):

        self.response.headers["Content-Type"] = "application/json"

        request_stats = RequestStats.get(self.request.get("request_id"))
        if not request_stats:
            return

        dict_request_stats = {}
        for property in RequestStats.serialized_properties:
            dict_request_stats[property] = request_stats.__getattribute__(property)

        self.response.out.write(simplejson.dumps(dict_request_stats))

class RequestStats(object):

    serialized_properties = ["request_id", "url", "url_short", "s_dt", "profiler_results", "appstats_results"]

    def __init__(self, request_id, environ, middleware):
        self.request_id = request_id

        self.url = environ.get("PATH_INFO")
        if environ.get("QUERY_STRING"):
            self.url += "?%s" % environ.get("QUERY_STRING")

        self.url_short = self.url
        if len(self.url_short) > 26:
            self.url_short = self.url_short[:26] + "..."

        self.s_dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.profiler_results = RequestStats.calc_profiler_results(middleware)
        self.appstats_results = RequestStats.calc_appstats_results(middleware)

    def store(self):
        # Store compressed results so we stay under the memcache 1MB limit
        pickled = pickle.dumps(self)
        compressed_pickled = zlib.compress(pickled)

        return memcache.set(RequestStats.memcache_key(self.request_id), compressed_pickled)

    @staticmethod
    def get(request_id):
        if request_id:

            compressed_pickled = memcache.get(RequestStats.memcache_key(request_id))

            if compressed_pickled:
                pickled = zlib.decompress(compressed_pickled)
                return pickle.loads(pickled)

        return None

    @staticmethod
    def memcache_key(request_id):
        if not request_id:
            return None
        return "__gae_mini_profiler_request_%s" % request_id

    @staticmethod
    def seconds_fmt(f):
        return RequestStats.milliseconds_fmt(f * 1000)

    @staticmethod
    def milliseconds_fmt(f):
        return ("%.5f" % f).rstrip("0").rstrip(".")

    @staticmethod
    def short_method_fmt(s):
        return s[s.rfind("/") + 1:]

    @staticmethod
    def short_rpc_file_fmt(s):
        if not s:
            return ""
        return s[s.find("/"):]

    @staticmethod
    def calc_profiler_results(middleware):
        import pstats

        # Make sure nothing is printed to stdout
        output = StringIO.StringIO()
        stats = pstats.Stats(middleware.prof, stream=output)
        stats.sort_stats("cumulative")

        results = {
            "total_call_count": stats.total_calls,
            "total_time": RequestStats.seconds_fmt(stats.total_tt),
            "calls": []
        }

        width, list_func_names = stats.get_print_list([80])
        for func_name in list_func_names:
            primitive_call_count, total_call_count, total_time, cumulative_time, callers = stats.stats[func_name]

            func_desc = pstats.func_std_string(func_name)

            callers_names = map(lambda func_name: pstats.func_std_string(func_name), callers.keys())
            callers_desc = map(
                    lambda name: {"func_desc": name, "func_desc_short": RequestStats.short_method_fmt(name)}, 
                    callers_names)

            results["calls"].append({
                "primitive_call_count": primitive_call_count, 
                "total_call_count": total_call_count, 
                "total_time": RequestStats.seconds_fmt(total_time), 
                "per_call": RequestStats.seconds_fmt(total_time / total_call_count) if total_call_count else "",
                "cumulative_time": RequestStats.seconds_fmt(cumulative_time), 
                "per_call_cumulative": RequestStats.seconds_fmt(cumulative_time / primitive_call_count) if primitive_call_count else "",
                "func_desc": func_desc,
                "func_desc_short": RequestStats.short_method_fmt(func_desc),
                "callers_desc": callers_desc,
            })

        output.close()

        return results
        
    @staticmethod
    def calc_appstats_results(middleware):
        if middleware.recorder:

            total_call_count = 0
            total_time = 0
            calls = []
            service_totals_dict = {}
            likely_dupes = False

            dict_requests = {}

            appstats_key = long(middleware.recorder.start_timestamp * 1000)

            for trace in middleware.recorder.traces:
                total_call_count += 1
                total_time += trace.duration_milliseconds()

                service_prefix = trace.service_call_name()

                if "." in service_prefix:
                    service_prefix = service_prefix[:service_prefix.find(".")]

                if not service_totals_dict.has_key(service_prefix):
                    service_totals_dict[service_prefix] = {"total_call_count": 0, "total_time": 0}

                service_totals_dict[service_prefix]["total_call_count"] += 1
                service_totals_dict[service_prefix]["total_time"] += trace.duration_milliseconds()

                stack_frames_desc = []
                for frame in trace.call_stack_:
                    stack_frames_desc.append("%s:%s %s" % 
                            (RequestStats.short_rpc_file_fmt(frame.class_or_file_name()), 
                                frame.line_number(), 
                                frame.function_name()))

                request = trace.request_data_summary()
                request_short = request
                if len(request_short) > 100:
                    request_short = request_short[:100] + "..."

                likely_dupe = dict_requests.has_key(request)
                likely_dupes = likely_dupes or likely_dupe

                dict_requests[request] = True

                response = trace.response_data_summary()[:100]

                calls.append({
                    "service": trace.service_call_name(),
                    "start_offset": RequestStats.milliseconds_fmt(trace.start_offset_milliseconds()),
                    "total_time": RequestStats.milliseconds_fmt(trace.duration_milliseconds()),
                    "request": request,
                    "request_short": request_short,
                    "response": response,
                    "stack_frames_desc": stack_frames_desc,
                    "likely_dupe": likely_dupe,
                })

            service_totals = []
            for service_prefix in service_totals_dict:
                service_totals.append({
                    "service_prefix": service_prefix,
                    "total_call_count": service_totals_dict[service_prefix]["total_call_count"],
                    "total_time": RequestStats.milliseconds_fmt(service_totals_dict[service_prefix]["total_time"]),
                })
            service_totals = sorted(service_totals, reverse=True, key=lambda service_total: float(service_total["total_time"]))

            return  {
                        "total_call_count": total_call_count,
                        "total_time": RequestStats.milliseconds_fmt(total_time),
                        "calls": calls,
                        "service_totals": service_totals,
                        "likely_dupes": likely_dupes,
                        "appstats_key": appstats_key,
                    }

        return None

class ProfilerWSGIMiddleware(object):

    def __init__(self, app):
        self.app = app
        self.app_clean = app
        self.prof = None
        self.recorder = None

    def __call__(self, environ, start_response):

        global request_id
        request_id = None

        # Start w/ a non-profiled app at the beginning of each request
        self.app = self.app_clean
        self.prof = None
        self.recorder = None

        if self.should_profile(environ):

            # Set a random ID for this request so we can look up stats later
            import base64
            import os
            request_id = base64.urlsafe_b64encode(os.urandom(15))

            # Send request id in headers so jQuery ajax calls can pick
            # up profiles.
            def profiled_start_response(status, headers, exc_info = None):
                headers.append(("X-MiniProfiler-Id", request_id))
                return start_response(status, headers, exc_info)

            # Configure AppStats output, keeping a high level of request
            # content so we can detect dupe RPCs more accurately
            from google.appengine.ext.appstats import recording
            recording.config.MAX_REPR = 750

            # Turn on AppStats monitoring for this request
            old_app = self.app
            def wrapped_appstats_app(environ, start_response):
                # Use this wrapper to grab the app stats recorder for RequestStats.save()
                self.recorder = recording.recorder
                return old_app(environ, start_response)
            self.app = recording.appstats_wsgi_middleware(wrapped_appstats_app)

            # Turn on cProfile profiling for this request
            import cProfile
            self.prof = cProfile.Profile()

            # Get profiled wsgi result
            result = self.prof.runcall(lambda *args, **kwargs: self.app(environ, profiled_start_response), None, None)

            self.recorder = recording.recorder

            # If we're dealing w/ a generator, profile all of the .next calls as well
            if type(result) == GeneratorType:

                while True:
                    try:
                        yield self.prof.runcall(result.next)
                    except StopIteration:
                        break

            else:
                for value in result:
                    yield value

            # Store stats for later access
            RequestStats(request_id, environ, self).store()

            # Just in case we're using up memory in the recorder and profiler
            self.recorder = None
            self.prof = None
            request_id = None

        else:
            result = self.app(environ, start_response)
            for value in result:
                yield value
