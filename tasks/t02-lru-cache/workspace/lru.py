class LRUCache:
    """A fixed-capacity cache that evicts the least recently used entry."""

    def __init__(self, capacity):
        """Create a cache holding at most `capacity` items."""
        raise NotImplementedError

    def get(self, key):
        """Return the value for `key`, or None. Counts as a use of `key`."""
        raise NotImplementedError

    def put(self, key, value):
        """Insert or update `key`. Counts as a use. Evicts LRU entry if full."""
        raise NotImplementedError

    def __len__(self):
        """Return the number of items currently held."""
        raise NotImplementedError
