import threading


class MetricsRegistry:
    """Thread-safe counters with change notifications.

    The lock protects the counter map only. Subscribers are collected under the
    lock and then invoked with it released, so a subscriber may call back into
    the registry and a slow subscriber cannot stall other threads.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._counters = {}
        self._subscribers = []

    def subscribe(self, fn):
        with self._lock:
            self._subscribers.append(fn)

    def _bump(self, name, value):
        self._counters[name] = self._counters.get(name, 0) + value
        return self._counters[name]

    def _notify(self, subscribers, events):
        for name, value in events:
            for fn in subscribers:
                fn(name, value)

    def record(self, name, value=1):
        with self._lock:
            current = self._bump(name, value)
            subscribers = list(self._subscribers)
        self._notify(subscribers, [(name, current)])

    def record_many(self, pairs):
        events = []
        with self._lock:
            subscribers = list(self._subscribers)
            for name, value in pairs:
                events.append((name, self._bump(name, value)))
        self._notify(subscribers, events)

    def snapshot(self):
        with self._lock:
            return dict(self._counters)

    def reset(self):
        with self._lock:
            self._counters.clear()
