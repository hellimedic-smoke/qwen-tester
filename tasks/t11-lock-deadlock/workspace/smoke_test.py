import threading
from metrics import MetricsRegistry

r = MetricsRegistry()
done = threading.Event()


def go():
    r.record_many([("hits", 1), ("hits", 2)])
    done.set()


threading.Thread(target=go, daemon=True).start()
assert done.wait(timeout=5), "record_many() deadlocked"
assert r.snapshot() == {"hits": 3}, r.snapshot()
print("smoke tests passed")
