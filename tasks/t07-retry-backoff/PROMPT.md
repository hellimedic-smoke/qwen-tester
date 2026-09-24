Implement `retry()` in `retry.py` following the docstring in the file.

`retry(fn, attempts=3, base_delay=1.0, max_delay=30.0, sleep=time.sleep, rand=random.random)`

- Calls `fn()` and returns its result as soon as it succeeds.
- If `fn()` raises, retry until `fn` has been called `attempts` times in total.
- Before retry number `k` (k = 1 for the first retry), wait
  `min(base_delay * 2 ** (k - 1), max_delay)` seconds, scaled by a jitter factor
  of `0.5 + 0.5 * rand()` — so the actual wait is between 50% and 100% of that
  value. Perform the wait by calling `sleep(seconds)`.
- Never sleep after the final attempt — if the last attempt fails, raise
  immediately.
- If every attempt fails, re-raise the exception from the last attempt.
- `attempts < 1` raises `ValueError`.

The `sleep` and `rand` parameters exist so tests can inject fakes; always call
them rather than `time.sleep` / `random.random` directly. Do not change the
signature.
