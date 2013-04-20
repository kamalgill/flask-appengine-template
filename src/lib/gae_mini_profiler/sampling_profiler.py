"""CPU profiler that works by sampling the call stack periodically.

This profiler provides a very simplistic view of where your request is spending
its time. It does this by periodically sampling your request's call stack to
figure out in which functions real time is being spent.

PRO: since the profiler only samples the call stack occasionally, it has much
less overhead than an instrumenting profiler, and avoids biases that
instrumenting profilers have due to instrumentation overhead (which causes
instrumenting profilers to overstate how much time is spent in frequently
called functions, or functions with deep call stacks).

CON: since the profiler only samples, it does not allow you to accurately
answer a question like, "how much time was spent in routine X?", especially if
routine X takes relatively little time.  (You *can* answer questions like "what
is the ratio of time spent in routine X vs routine Y," at least if both
routines take a reasonable amount of time.)  It is better suited for answering
the question, "Where is the time spent by my app?"
"""

from collections import defaultdict
import logging
import os
import sys
import time
import threading
import traceback

from gae_mini_profiler import util

_is_dev_server = os.environ["SERVER_SOFTWARE"].startswith("Devel")

class InspectingThread(threading.Thread):
    """Thread that periodically triggers profiler inspections."""
    SAMPLES_PER_SECOND = 250

    def __init__(self, profile=None):
        super(InspectingThread, self).__init__()
        self._stop_event = threading.Event()
        self.profile = profile

    def stop(self):
        """Stop this thread."""
        # http://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread-in-python
        self._stop_event.set()

    def should_stop(self):
        return self._stop_event.is_set()

    def run(self):
        """Start periodic profiler inspections.
        
        This will run, periodically inspecting and then sleeping, until
        manually stopped via stop()."""
        # Keep sampling until this thread is explicitly stopped.
        while not self.should_stop():

            # Take a sample of the main request thread's frame stack...
            self.profile.take_sample()

            # ...then sleep and let it do some more work.
            time.sleep(1.0 / InspectingThread.SAMPLES_PER_SECOND)

            # Only take one sample per thread if this is running on the
            # single-threaded dev server.
            if _is_dev_server and len(self.profile.samples) > 0:
                break


class ProfileSample(object):
    """Single stack trace sample gathered during a periodic inspection."""
    def __init__(self, stack):
        self.stack_trace = traceback.extract_stack(stack)


class Profile(object):
    """Profiler that periodically inspects a request and logs stack traces."""
    def __init__(self):
        # All saved stack trace samples
        self.samples = []

        # Thread id for the request thread currently being profiled
        self.current_request_thread_id = None

        # Thread that constantly waits, inspects, waits, inspect, ...
        self.inspecting_thread = None

    def results(self):
        """Return sampling results in a dictionary for template context."""
        aggregated_calls = defaultdict(int)
        total_samples = len(self.samples)

        for sample in self.samples:
            for filename, line_num, function_name, src in sample.stack_trace:
                aggregated_calls["%s\n\n%s:%s (%s)" %
                        (src, filename, line_num, function_name)] += 1

        # Turn aggregated call samples into dictionary of results
        calls = [{
            "func_desc": item[0],
            "func_desc_short": util.short_method_fmt(item[0]),
            "count_samples": item[1],
            "per_samples": "%s%%" % util.decimal_fmt(
                100.0 * item[1] / total_samples),
            } for item in aggregated_calls.items()]

        # Sort call sample results by # of times calls appeared in a sample
        calls = sorted(calls, reverse=True,
            key=lambda call: call["count_samples"])

        return {
                "calls": calls,
                "total_samples": total_samples,
                "is_dev_server": _is_dev_server,
            }

    def take_sample(self):
        # Look at stacks of all existing threads...
        # See http://bzimmer.ziclix.com/2008/12/17/python-thread-dumps/
        for thread_id, stack in sys._current_frames().items():

            # ...but only sample from the main request thread.

            if _is_dev_server:
                # In development, current_request_thread_id won't be set
                # properly. threading.current_thread().ident always returns -1
                # in dev. So instead, we just take a peek at the stack's
                # current package to figure out if it is the request thread.
                # Even though the dev server is single-threaded,
                # sys._current_frames will return multiple threads, because
                # some of them are spawned by the App Engine dev server for
                # internal purposes. We don't want to sample these internal dev
                # server threads -- we want to sample the thread that is
                # running the current request. Since the dev server will be
                # running this sampling code immediately from the run() code
                # below, we can spot this thread's stack by looking at its
                # global namespace (f_globals) and making sure it's currently
                # in the gae_mini_profiler package.
                should_sample = (stack.f_globals["__package__"] ==
                        "gae_mini_profiler")
            else:
                # In production, current_request_thread_id will be set properly
                # by threading.current_thread().ident.
                # TODO(kamens): this profiler will need work if we ever
                # actually use multiple threads in a single request and want to
                # profile more than one of them.
                should_sample = thread_id == self.current_request_thread_id

            if should_sample:
                # Grab a sample of this thread's current stack
                self.samples.append(ProfileSample(stack))

    def run(self, fxn):
        """Run function with samping profiler enabled, saving results."""
        if not hasattr(threading, "current_thread"):
            # Sampling profiler is not supported in Python2.5
            logging.warn("The sampling profiler is not supported in Python2.5")
            return fxn()

        # Store the thread id for the current request's thread. This lets
        # the inspecting thread know which thread to inspect.
        self.current_request_thread_id = threading.current_thread().ident

        # Start the thread that will be periodically inspecting the frame
        # stack of this current request thread
        self.inspecting_thread = InspectingThread(profile=self)
        self.inspecting_thread.start()

        try:
            # Run the request fxn which will be inspected by the inspecting
            # thread.
            return fxn()
        finally:
            # Stop and clear the inspecting thread
            self.inspecting_thread.stop()
            self.inspecting_thread = None
