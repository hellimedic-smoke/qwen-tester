`metrics.py` is a metrics registry shared by every worker thread in the
service. Three incidents have been traced back to it:

1. Any call to `record_many()` hangs forever.
2. A subscriber that reads the registry — calling `snapshot()` to compute a
   derived metric, say — hangs the thread that recorded the metric.
3. One slow subscriber (one that does network I/O, for instance) stalls every
   other thread in the service, even threads only reading metrics.

Fix all three while keeping the registry thread-safe:
- `record`, `record_many`, `snapshot`, `reset` and `subscribe` must all remain
  safe to call concurrently from many threads, and counts must never be lost.
- Subscribers must still be notified for every recorded metric, receiving the
  name and the counter's value as of that record.
- A subscriber must be able to call back into the registry.
- A slow subscriber must not block other threads from using the registry.

Keep the class name and the public method signatures as they are.
