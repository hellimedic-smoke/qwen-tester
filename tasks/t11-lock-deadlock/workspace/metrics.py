import threading


class MetricsRegistry:
    """Thread-safe counters with change notifications."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters = {}
        self._subscribers = []

    def subscribe(self, fn):
        """Register fn(name, value), called after every record."""
        with self._lock:
            self._subscribers.append(fn)

    def record(self, name, value=1):
        """Add `value` to the counter `name` and notify subscribers."""
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value
            current = self._counters[name]
            for fn in self._subscribers:
                fn(name, current)

    def record_many(self, pairs):
        """Record a batch of (name, value) pairs."""
        with self._lock:
            for name, value in pairs:
                self.record(name, value)

    def snapshot(self):
        """Return a copy of the current counters."""
        with self._lock:
            return dict(self._counters)

    def reset(self):
        with self._lock:
            self._counters.clear()
