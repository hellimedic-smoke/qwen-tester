import random
import time


def retry(fn, attempts=3, base_delay=1.0, max_delay=30.0, sleep=time.sleep, rand=random.random):
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception:
            if attempt == attempts:
                raise
            delay = min(base_delay * 2 ** (attempt - 1), max_delay)
            sleep(delay * (0.5 + 0.5 * rand()))
