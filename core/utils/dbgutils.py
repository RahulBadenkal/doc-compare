from functools import wraps
import time
from datetime import datetime

_total_time_call_stack = [0]  # Global variable to track partial execution time for a function


# TODO: Should we pass a DEBUG flag to time tracker?
def time_tracker(fn, debug=False):
    @wraps(fn)
    def _advanced_time_tracker(*args, **kwargs):
        if not debug:
            return fn(*args, **kwargs)

        global _total_time_call_stack
        _total_time_call_stack.append(0)

        start_time = time.time()

        print(
            "[FUNC ENTER] {} @ {}".format(fn.__name__, datetime.today())
        )

        try:
            result = fn(*args, **kwargs)
        finally:
            elapsed_time = time.time() - start_time
            inner_total_time = _total_time_call_stack.pop()
            partial_time = elapsed_time - inner_total_time

            _total_time_call_stack[-1] += elapsed_time

        print(
            "[FUNC EXIT] {}. {:.3f}s, {:.3f}s".format(fn.__name__, elapsed_time, partial_time)
        )

        return result

    return _advanced_time_tracker


