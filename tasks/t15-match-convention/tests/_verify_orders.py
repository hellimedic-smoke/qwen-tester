import unittest

from api import _data
from api.errors import ApiError
from api.orders import list_orders
from api.pagination import DEFAULT_LIMIT, MAX_LIMIT, encode_cursor


class TestMatchesConvention(unittest.TestCase):
    """Whatever list_users does, list_orders must do the same way."""

    def test_accepts_limit_and_cursor_keywords(self):
        try:
            list_orders(limit=5, cursor=None)
        except TypeError as e:
            self.fail(f"list_orders must take `limit` and `cursor` keywords: {e}")

    def test_response_shape(self):
        page = list_orders(limit=5)
        self.assertEqual(set(page), {"items", "next_cursor"})
        self.assertEqual(len(page["items"]), 5)
        self.assertIsNotNone(page["next_cursor"])

    def test_default_limit(self):
        self.assertEqual(len(list_orders()["items"]), DEFAULT_LIMIT)

    def test_limit_is_capped(self):
        self.assertLessEqual(len(list_orders(limit=10_000)["items"]), MAX_LIMIT)

    def test_ordered_by_id(self):
        ids = [r["id"] for r in list_orders(limit=MAX_LIMIT)["items"]]
        self.assertEqual(ids, sorted(ids))

    def test_last_page_has_no_next_cursor(self):
        self.assertIsNone(list_orders(limit=MAX_LIMIT)["next_cursor"])

    def test_invalid_limit_raises_api_error(self):
        for bad in (0, -1):
            with self.assertRaises(ApiError) as ctx:
                list_orders(limit=bad)
            self.assertEqual(ctx.exception.code, "invalid_limit")

    def test_invalid_cursor_raises_api_error(self):
        with self.assertRaises(ApiError) as ctx:
            list_orders(cursor="!!!not-base64!!!")
        self.assertEqual(ctx.exception.code, "invalid_cursor")

    def test_cursor_for_unknown_row_raises_api_error(self):
        with self.assertRaises(ApiError) as ctx:
            list_orders(cursor=encode_cursor("o-999"))
        self.assertEqual(ctx.exception.code, "invalid_cursor")

    def test_cursor_is_opaque_not_a_raw_offset(self):
        cur = list_orders(limit=5)["next_cursor"]
        self.assertIsInstance(cur, str)
        self.assertFalse(cur.isdigit(), "cursor must be opaque, not a bare offset")


class TestTraversal(unittest.TestCase):
    def _walk(self, limit):
        seen, cursor, pages = [], None, 0
        while True:
            page = list_orders(limit=limit, cursor=cursor)
            seen.extend(r["id"] for r in page["items"])
            cursor = page["next_cursor"]
            pages += 1
            self.assertLess(pages, 200, "pagination did not terminate")
            if cursor is None:
                return seen

    def test_full_traversal_sees_everything_once(self):
        seen = self._walk(10)
        expected = sorted(r["id"] for r in _data.ORDERS)
        self.assertEqual(seen, expected)
        self.assertEqual(len(seen), len(set(seen)), "a row was returned twice")

    def test_traversal_with_limit_of_one(self):
        self.assertEqual(len(self._walk(1)), len(_data.ORDERS))


class TestKeysetStability(unittest.TestCase):
    """The reference implementation is keyset-based, so an insert behind the
    cursor must not shift the window."""

    def setUp(self):
        self._orig = list(_data.ORDERS)

    def tearDown(self):
        _data.ORDERS[:] = self._orig

    def test_insert_behind_cursor_does_not_skip_rows(self):
        first = list_orders(limit=10)
        cursor = first["next_cursor"]
        _data.ORDERS.append({"id": "o-000", "customer": "u-001", "total": 0})
        second = list_orders(limit=10, cursor=cursor)
        expected = sorted(r["id"] for r in self._orig)[10:20]
        self.assertEqual([r["id"] for r in second["items"]], expected,
                         "an insert before the cursor shifted the page window")


class TestUsersUntouched(unittest.TestCase):
    def test_users_still_works(self):
        from api.users import list_users
        page = list_users(limit=3)
        self.assertEqual([r["id"] for r in page["items"]], ["u-001", "u-002", "u-003"])
        self.assertIsNotNone(page["next_cursor"])
