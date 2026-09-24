import random
import time


def retry(fn, attempts=3, base_delay=1.0, max_delay=30.0, sleep=time.sleep, rand=random.random):
    """Call fn(), retrying with exponential backoff and jitter on failure.

    Returns fn()'s result, or re-raises the last exception if every attempt
    fails. See PROMPT.md for the exact backoff schedule.
    """
    raise NotImplementedError
