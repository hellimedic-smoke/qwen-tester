import unittest
from pagination import paginate


class TestPaginate(unittest.TestCase):
    def test_even_division(self):
        r = paginate(list(range(20)), 1, 10)
        self.assertEqual(r["total_pages"], 2)
        self.assertEqual(r["items"], list(range(10)))
        self.assertTrue(r["has_next"])
        self.assertFalse(r["has_prev"])

    def test_last_page_of_even_division(self):
        r = paginate(list(range(20)), 2, 10)
        self.assertEqual(r["items"], list(range(10, 20)))
        self.assertFalse(r["has_next"])
        self.assertTrue(r["has_prev"])

    def test_partial_last_page(self):
        r = paginate(list(range(25)), 3, 10)
        self.assertEqual(r["total_pages"], 3)
        self.assertEqual(r["items"], list(range(20, 25)))
        self.assertFalse(r["has_next"])

    def test_empty_result_set(self):
        r = paginate([], 1, 10)
        self.assertEqual(r["total_pages"], 1)
        self.assertEqual(r["items"], [])
        self.assertEqual(r["total"], 0)
        self.assertFalse(r["has_next"])
        self.assertFalse(r["has_prev"])

    def test_single_page(self):
        r = paginate([1, 2, 3], 1, 10)
        self.assertEqual(r["total_pages"], 1)
        self.assertFalse(r["has_next"])
        self.assertFalse(r["has_prev"])

    def test_page_past_end_raises(self):
        with self.assertRaises(ValueError):
            paginate(list(range(20)), 3, 10)
        with self.assertRaises(ValueError):
            paginate([], 2, 10)

    def test_page_below_one_raises(self):
        with self.assertRaises(ValueError):
            paginate(list(range(20)), 0, 10)
        with self.assertRaises(ValueError):
            paginate(list(range(20)), -1, 10)

    def test_bad_per_page_raises(self):
        with self.assertRaises(ValueError):
            paginate(list(range(20)), 1, 0)
        with self.assertRaises(ValueError):
            paginate(list(range(20)), 1, -5)

    def test_keys_preserved(self):
        r = paginate(list(range(5)), 1, 10)
        self.assertEqual(
            set(r), {"items", "page", "per_page", "total", "total_pages", "has_next", "has_prev"}
        )
