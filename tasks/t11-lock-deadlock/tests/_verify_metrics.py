import threading
import time
import unittest

from metrics import MetricsRegistry


def run_with_timeout(fn, timeout=5.0):
    """Run fn() in a thread; return (finished, result). Never hangs the suite."""
    box = {}

    def target():
        try:
            box["result"] = fn()
        except BaseException as exc:
            box["error"] = exc

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return False, None
    if "error" in box:
        raise box["error"]
    return True, box.get("result")


class TestBasics(unittest.TestCase):
    def setUp(self):
        self.r = MetricsRegistry()

    def test_record_and_snapshot(self):
        self.r.record("hits")
        self.r.record("hits", 4)
        self.r.record("misses", 2)
        self.assertEqual(self.r.snapshot(), {"hits": 5, "misses": 2})

    def test_snapshot_is_a_copy(self):
        self.r.record("a")
        snap = self.r.snapshot()
        snap["a"] = 999
        self.assertEqual(self.r.snapshot()["a"], 1)

    def test_reset(self):
        self.r.record("a")
        self.r.reset()
        self.assertEqual(self.r.snapshot(), {})

    def test_subscribers_notified(self):
        seen = []
        self.r.subscribe(lambda name, value: seen.append((name, value)))
        self.r.record("a")
        self.r.record("a", 2)
        self.r.record("b", 5)
        self.assertEqual(seen, [("a", 1), ("a", 3), ("b", 5)])

    def test_multiple_subscribers(self):
        one, two = [], []
        self.r.subscribe(lambda n, v: one.append(v))
        self.r.subscribe(lambda n, v: two.append(v))
        self.r.record("a", 7)
        self.assertEqual(one, [7])
        self.assertEqual(two, [7])


class TestIncident1RecordMany(unittest.TestCase):
    def setUp(self):
        self.r = MetricsRegistry()

    def test_record_many_completes(self):
        ok, _ = run_with_timeout(lambda: self.r.record_many([("a", 1), ("b", 2)]))
        self.assertTrue(ok, "record_many() deadlocked")

    def test_record_many_values(self):
        ok, _ = run_with_timeout(lambda: self.r.record_many([("a", 1), ("a", 2), ("b", 5)]))
        self.assertTrue(ok, "record_many() deadlocked")
        self.assertEqual(self.r.snapshot(), {"a": 3, "b": 5})

    def test_record_many_notifies(self):
        seen = []
        self.r.subscribe(lambda n, v: seen.append((n, v)))
        ok, _ = run_with_timeout(lambda: self.r.record_many([("a", 1), ("a", 2)]))
        self.assertTrue(ok, "record_many() deadlocked")
        self.assertEqual(seen, [("a", 1), ("a", 3)])


class TestIncident2ReentrantSubscriber(unittest.TestCase):
    def setUp(self):
        self.r = MetricsRegistry()

    def test_subscriber_may_read_snapshot(self):
        seen = []
        self.r.subscribe(lambda n, v: seen.append(self.r.snapshot()))
        ok, _ = run_with_timeout(lambda: self.r.record("a"))
        self.assertTrue(ok, "a subscriber calling snapshot() deadlocked the recorder")
        self.assertEqual(seen, [{"a": 1}])

    def test_subscriber_may_record(self):
        self.r.subscribe(lambda n, v: self.r.record("derived") if n != "derived" else None)
        ok, _ = run_with_timeout(lambda: self.r.record("a"))
        self.assertTrue(ok, "a subscriber calling record() deadlocked the recorder")
        self.assertEqual(self.r.snapshot(), {"a": 1, "derived": 1})


class TestIncident3SlowSubscriber(unittest.TestCase):
    def setUp(self):
        self.r = MetricsRegistry()

    def test_slow_subscriber_does_not_block_readers(self):
        entered = threading.Event()
        release = threading.Event()

        def slow(name, value):
            # Only the first record parks; otherwise the later record() below
            # would be stalled by the subscriber itself rather than by a lock.
            if name == "a":
                entered.set()
                release.wait(timeout=10)

        self.r.subscribe(slow)
        recorder = threading.Thread(target=lambda: self.r.record("a"), daemon=True)
        recorder.start()
        self.assertTrue(entered.wait(timeout=5), "subscriber was never called")

        # The recorder is now parked inside the subscriber. Another thread must
        # still be able to use the registry.
        try:
            ok, snap = run_with_timeout(self.r.snapshot, timeout=3.0)
            self.assertTrue(ok, "a slow subscriber blocked another thread's snapshot()")
            ok2, _ = run_with_timeout(lambda: self.r.record("b"), timeout=3.0)
            self.assertTrue(ok2, "a slow subscriber blocked another thread's record()")
        finally:
            release.set()
            recorder.join(timeout=5)

    def test_counts_survive_the_slow_subscriber(self):
        release = threading.Event()
        entered = threading.Event()
        def slow(name, value):
            if name == "a":
                entered.set()
                release.wait(timeout=10)

        self.r.subscribe(slow)
        recorder = threading.Thread(target=lambda: self.r.record("a"), daemon=True)
        recorder.start()
        self.assertTrue(entered.wait(timeout=5))
        try:
            run_with_timeout(lambda: self.r.record("b"), timeout=3.0)
        finally:
            release.set()
            recorder.join(timeout=5)
        self.assertEqual(self.r.snapshot(), {"a": 1, "b": 1})


class TestConcurrentCorrectness(unittest.TestCase):
    def test_no_lost_counts_under_load(self):
        r = MetricsRegistry()
        threads = 16
        per_thread = 500

        def worker():
            for _ in range(per_thread):
                r.record("hits")

        ts = [threading.Thread(target=worker) for _ in range(threads)]
        for t in ts:
            t.start()
        for t in ts:
            t.join(timeout=60)
        self.assertFalse(any(t.is_alive() for t in ts), "recording deadlocked under load")
        self.assertEqual(r.snapshot()["hits"], threads * per_thread, "counts were lost")

    def test_concurrent_readers_and_writers(self):
        r = MetricsRegistry()
        stop = threading.Event()
        errors = []

        def reader():
            try:
                while not stop.is_set():
                    r.snapshot()
            except Exception as exc:
                errors.append(exc)

        def writer():
            try:
                for _ in range(2000):
                    r.record("x")
            except Exception as exc:
                errors.append(exc)

        rs = [threading.Thread(target=reader) for _ in range(4)]
        ws = [threading.Thread(target=writer) for _ in range(4)]
        for t in rs + ws:
            t.start()
        for t in ws:
            t.join(timeout=60)
        stop.set()
        for t in rs:
            t.join(timeout=10)
        self.assertEqual(errors, [])
        self.assertEqual(r.snapshot()["x"], 8000)
