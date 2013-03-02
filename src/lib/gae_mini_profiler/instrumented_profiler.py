"""CPU profiler that works by instrumenting all function calls (uses cProfile).

This profiler provides detailed function timings for all function calls
during a request.

This is just a simple wrapper for cProfile with result formatting. See
http://docs.python.org/2/library/profile.html for more.

PRO: since every function call is instrumented, you'll be sure to see
everything that goes on during a request. For code that doesn't have lots of
deeply nested function calls, this can be the easiest and most accurate way to
get an idea for which functions are taking lots of time.

CON: overhead is added to each function call due to this instrumentation. If
you're profiling code with deeply nested function calls or tight loops going
over lots of function calls, this perf overhead will add up.
"""

import cProfile
import pstats
import StringIO

import util

class Profile(object):
    """Profiler that wraps cProfile for programmatic access and reporting."""
    def __init__(self):
        self.c_profile = cProfile.Profile()

    def results(self):
        """Return cProfile results in a dictionary for template context."""
        # Make sure nothing is printed to stdout
        output = StringIO.StringIO()
        stats = pstats.Stats(self.c_profile, stream=output)
        stats.sort_stats("cumulative")

        results = {
            "total_call_count": stats.total_calls,
            "total_time": util.seconds_fmt(stats.total_tt),
            "calls": []
        }

        width, list_func_names = stats.get_print_list([80])
        for func_name in list_func_names:
            primitive_call_count, total_call_count, total_time, cumulative_time, callers = stats.stats[func_name]

            func_desc = pstats.func_std_string(func_name)

            callers_names = map(lambda func_name: pstats.func_std_string(func_name), callers.keys())
            callers_desc = map(
                    lambda name: {"func_desc": name, "func_desc_short": util.short_method_fmt(name)},
                    callers_names)

            results["calls"].append({
                "primitive_call_count": primitive_call_count,
                "total_call_count": total_call_count,
                "cumulative_time": util.seconds_fmt(cumulative_time, 2),
                "per_call_cumulative": util.seconds_fmt(cumulative_time / primitive_call_count, 2) if primitive_call_count else "",
                "func_desc": func_desc,
                "func_desc_short": util.short_method_fmt(func_desc),
                "callers_desc": callers_desc,
            })

        output.close()

        return results

    def run(self, fxn):
        """Run function with cProfile enabled, saving results."""
        return self.c_profile.runcall(lambda *args, **kwargs: fxn(), None, None)
