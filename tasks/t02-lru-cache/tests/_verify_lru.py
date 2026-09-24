import time
import unittest
from lru import LRUCache


class TestLRUCache(unittest.TestCase):
    def test_basic_get_put(self):
        c = LRUCache(2)
        c.put("a", 1)
        self.assertEqual(c.get("a"), 1)
        self.assertIsNone(c.get("missing"))

    def test_len(self):
        c = LRUCache(3)
        self.assertEqual(len(c), 0)
        c.put("a", 1); c.put("b", 2)
        self.assertEqual(len(c), 2)

    def test_eviction_order(self):
        c = LRUCache(2)
        c.put("a", 1); c.put("b", 2); c.put("c", 3)
        self.assertIsNone(c.get("a"), "'a' was least recently used and should be evicted")
        self.assertEqual(c.get("b"), 2)
        self.assertEqual(c.get("c"), 3)

    def test_get_refreshes_recency(self):
        c = LRUCache(2)
        c.put("a", 1); c.put("b", 2)
        c.get("a")              # 'a' is now most recent, so 'b' is the victim
        c.put("c", 3)
        self.assertEqual(c.get("a"), 1)
        self.assertIsNone(c.get("b"))

    def test_put_existing_refreshes_and_updates(self):
        c = LRUCache(2)
        c.put("a", 1); c.put("b", 2)
        c.put("a", 99)          # update + refresh, must not grow the cache
        self.assertEqual(len(c), 2)
        c.put("c", 3)
        self.assertEqual(c.get("a"), 99)
        self.assertIsNone(c.get("b"))

    def test_capacity_zero(self):
        c = LRUCache(0)
        c.put("a", 1)
        self.assertEqual(len(c), 0)
        self.assertIsNone(c.get("a"))

    def test_negative_capacity(self):
        with self.assertRaises(ValueError):
            LRUCache(-1)

    def test_is_constant_time(self):
        c = LRUCache(50_000)
        for i in range(50_000):
            c.put(i, i)
        start = time.perf_counter()
        for i in range(50_000):
            c.get(i)
            c.put(i + 50_000, i)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 3.0, f"100k ops took {elapsed:.1f}s; implementation is not O(1)")
