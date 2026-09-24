Implement the `LRUCache` class in `lru.py` according to the docstrings already
in the file.

Requirements:
- `LRUCache(capacity)` holds at most `capacity` items.
- `get(key)` returns the value, or `None` if absent, and counts as a use.
- `put(key, value)` inserts or updates, and counts as a use.
- When full, inserting a new key evicts the least recently used key.
- `len(cache)` returns the current number of items.
- `get` and `put` must both be O(1) — do not scan the whole cache on each call.
- A capacity of 0 is legal: the cache then stores nothing.
- A negative capacity raises `ValueError`.

Do not change the class or method names.
