import unittest
from retry import retry


class Recorder:
    """Fake clock: records requested sleeps instead of performing them."""

    def __init__(self):
        self.sleeps = []

    def __call__(self, seconds):
        self.sleeps.append(seconds)


def failing(n, exc=RuntimeError):
    """A callable that fails its first n calls, then returns 'ok'."""
    state = {"calls": 0}

    def fn():
        state["calls"] += 1
        if state["calls"] <= n:
            raise exc(f"boom {state['calls']}")
        return "ok"

    fn.state = state
    return fn


class TestRetry(unittest.TestCase):
    def test_returns_immediately_on_success(self):
        s = Recorder()
        fn = failing(0)
        self.assertEqual(retry(fn, attempts=3, sleep=s, rand=lambda: 1.0), "ok")
        self.assertEqual(fn.state["calls"], 1)
        self.assertEqual(s.sleeps, [], "must not sleep when the first call succeeds")

    def test_retries_until_success(self):
        s = Recorder()
        fn = failing(2)
        self.assertEqual(retry(fn, attempts=5, sleep=s, rand=lambda: 1.0), "ok")
        self.assertEqual(fn.state["calls"], 3)
        self.assertEqual(len(s.sleeps), 2)

    def test_exponential_schedule_full_jitter(self):
        s = Recorder()
        retry(failing(3), attempts=4, base_delay=1.0, sleep=s, rand=lambda: 1.0)
        self.assertEqual(s.sleeps, [1.0, 2.0, 4.0])

    def test_jitter_halves_delay(self):
        s = Recorder()
        retry(failing(2), attempts=3, base_delay=2.0, sleep=s, rand=lambda: 0.0)
        self.assertEqual(s.sleeps, [1.0, 2.0], "rand()==0 should give 50% of the delay")

    def test_max_delay_caps_growth(self):
        s = Recorder()
        retry(failing(4), attempts=5, base_delay=1.0, max_delay=3.0, sleep=s, rand=lambda: 1.0)
        self.assertEqual(s.sleeps, [1.0, 2.0, 3.0, 3.0])

    def test_no_sleep_after_final_attempt(self):
        s = Recorder()
        with self.assertRaises(RuntimeError):
            retry(failing(99), attempts=3, sleep=s, rand=lambda: 1.0)
        self.assertEqual(len(s.sleeps), 2, "3 attempts means 2 waits, not 3")

    def test_reraises_last_exception(self):
        s = Recorder()
        fn = failing(99, exc=KeyError)
        with self.assertRaises(KeyError):
            retry(fn, attempts=2, sleep=s, rand=lambda: 1.0)
        self.assertEqual(fn.state["calls"], 2)

    def test_single_attempt_never_sleeps(self):
        s = Recorder()
        with self.assertRaises(RuntimeError):
            retry(failing(99), attempts=1, sleep=s, rand=lambda: 1.0)
        self.assertEqual(s.sleeps, [])

    def test_invalid_attempts(self):
        with self.assertRaises(ValueError):
            retry(failing(0), attempts=0)
        with self.assertRaises(ValueError):
            retry(failing(0), attempts=-2)
