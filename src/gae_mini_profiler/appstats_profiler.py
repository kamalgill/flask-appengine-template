"""RPC profiler that uses appstats to track, time, and log all RPC events.

This is just a simple wrapper for appstats with result formatting. See
https://developers.google.com/appengine/docs/python/tools/appstats for more.
"""

import logging
from pprint import pformat

from google.appengine.ext.appstats import recording

import cleanup
import unformatter
import util

class Profile(object):
    """Profiler that wraps appstats for programmatic access and reporting."""
    def __init__(self):
        # Configure AppStats output, keeping a high level of request
        # content so we can detect dupe RPCs more accurately
        recording.config.MAX_REPR = 750

        # Each request has its own internal appstats recorder
        self.recorder = None

    def results(self):
        """Return appstats results in a dictionary for template context."""
        if not self.recorder:
            # If appstats fails to initialize for any reason, return an empty
            # set of results.
            logging.warn("Missing recorder for appstats profiler.")
            return {
                "calls": [],
                "total_time": 0,
            }

        total_call_count = 0
        total_time = 0
        calls = []
        service_totals_dict = {}
        likely_dupes = False
        end_offset_last = 0

        requests_set = set()

        appstats_key = long(self.recorder.start_timestamp * 1000)

        for trace in self.recorder.traces:
            total_call_count += 1

            total_time += trace.duration_milliseconds()

            # Don't accumulate total RPC time for traces that overlap asynchronously
            if trace.start_offset_milliseconds() < end_offset_last:
                total_time -= (end_offset_last - trace.start_offset_milliseconds())
            end_offset_last = trace.start_offset_milliseconds() + trace.duration_milliseconds()

            service_prefix = trace.service_call_name()

            if "." in service_prefix:
                service_prefix = service_prefix[:service_prefix.find(".")]

            if service_prefix not in service_totals_dict:
                service_totals_dict[service_prefix] = {
                    "total_call_count": 0,
                    "total_time": 0,
                    "total_misses": 0,
                }

            service_totals_dict[service_prefix]["total_call_count"] += 1
            service_totals_dict[service_prefix]["total_time"] += trace.duration_milliseconds()

            stack_frames_desc = []
            for frame in trace.call_stack_list():
                stack_frames_desc.append("%s:%s %s" %
                        (util.short_rpc_file_fmt(frame.class_or_file_name()),
                            frame.line_number(),
                            frame.function_name()))

            request = trace.request_data_summary()
            response = trace.response_data_summary()

            likely_dupe = request in requests_set
            likely_dupes = likely_dupes or likely_dupe
            requests_set.add(request)

            request_short = request_pretty = None
            response_short = response_pretty = None
            miss = 0
            try:
                request_object = unformatter.unformat(request)
                response_object = unformatter.unformat(response)

                request_short, response_short, miss = cleanup.cleanup(request_object, response_object)

                request_pretty = pformat(request_object)
                response_pretty = pformat(response_object)
            except Exception, e:
                logging.warning("Prettifying RPC calls failed.\n%s\nRequest: %s\nResponse: %s",
                    e, request, response, exc_info=True)

            service_totals_dict[service_prefix]["total_misses"] += miss

            calls.append({
                "service": trace.service_call_name(),
                "start_offset": util.milliseconds_fmt(trace.start_offset_milliseconds()),
                "total_time": util.milliseconds_fmt(trace.duration_milliseconds()),
                "request": request_pretty or request,
                "response": response_pretty or response,
                "request_short": request_short or cleanup.truncate(request),
                "response_short": response_short or cleanup.truncate(response),
                "stack_frames_desc": stack_frames_desc,
                "likely_dupe": likely_dupe,
            })

        service_totals = []
        for service_prefix in service_totals_dict:
            service_totals.append({
                "service_prefix": service_prefix,
                "total_call_count": service_totals_dict[service_prefix]["total_call_count"],
                "total_misses": service_totals_dict[service_prefix]["total_misses"],
                "total_time": util.milliseconds_fmt(service_totals_dict[service_prefix]["total_time"]),
            })
        service_totals = sorted(service_totals, reverse=True, key=lambda service_total: float(service_total["total_time"]))

        return  {
                    "total_call_count": total_call_count,
                    "total_time": util.milliseconds_fmt(total_time),
                    "calls": calls,
                    "service_totals": service_totals,
                    "likely_dupes": likely_dupes,
                    "appstats_key": appstats_key,
                }

    def wrap(self, app):
        """Wrap and return a WSGI application with appstats recording enabled.
        
        Args:
            app: existing WSGI application to be wrapped
        Returns:
            new WSGI application that will run the original app with appstats
                enabled.
        """
        def wrapped_appstats_app(environ, start_response):
            # Use this wrapper to grab the app stats recorder for RequestStats.save()
            if recording.recorder_proxy.has_recorder_for_current_request():
                self.recorder = recording.recorder_proxy.get_for_current_request()
            return app(environ, start_response)

        return recording.appstats_wsgi_middleware(wrapped_appstats_app)
