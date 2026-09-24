import os
import re
import unittest

from store import db, products, orders, customers, reports


def seed_via_modules():
    db.reset()
    products.add_product("A1", "Widget", 10)
    products.add_product("B2", "Gadget", 25)
    customers.add_customer("c1", "Ada")
    orders.place_order("o1", "c1", "A1", 3)
    orders.place_order("o2", "c1", "B2", 1)


class TestCompatibilityLayer(unittest.TestCase):
    """Existing module-level callers must keep working unchanged."""

    def setUp(self):
        seed_via_modules()

    def test_products(self):
        self.assertEqual(products.get_product("A1"),
                         {"sku": "A1", "name": "Widget", "price": 10})

    def test_orders(self):
        self.assertEqual(orders.get_order("o1")["total"], 30)

    def test_customer_orders(self):
        self.assertEqual({o["id"] for o in customers.customer_orders("c1")}, {"o1", "o2"})

    def test_report(self):
        r = reports.sales_report()
        self.assertEqual(r["orders"], 2)
        self.assertEqual(r["revenue"], 55)
        self.assertEqual(r["by_sku"][0], {"sku": "A1", "units": 3, "revenue": 30})

    def test_validation_preserved(self):
        with self.assertRaises(ValueError):
            products.add_product("X", "Bad", -1)
        with self.assertRaises(ValueError):
            orders.place_order("o9", "c1", "NOPE", 1)
        with self.assertRaises(ValueError):
            orders.place_order("o9", "nobody", "A1", 1)
        with self.assertRaises(ValueError):
            orders.place_order("o9", "c1", "A1", 0)


class TestStoreClass(unittest.TestCase):
    def _store(self):
        from store.store import Store
        return Store(db.Database())

    def test_store_exposes_operations(self):
        s = self._store()
        for name in ("add_product", "get_product", "place_order", "get_order",
                     "add_customer", "customer_orders", "sales_report"):
            self.assertTrue(callable(getattr(s, name, None)), f"Store.{name} missing")

    def test_store_round_trip(self):
        s = self._store()
        s.add_product("A1", "Widget", 10)
        s.add_customer("c1", "Ada")
        s.place_order("o1", "c1", "A1", 2)
        self.assertEqual(s.get_product("A1")["name"], "Widget")
        self.assertEqual(s.get_order("o1")["total"], 20)
        self.assertEqual(s.sales_report()["revenue"], 20)

    def test_store_validation(self):
        s = self._store()
        with self.assertRaises(ValueError):
            s.add_product("X", "Bad", -1)
        with self.assertRaises(ValueError):
            s.place_order("o1", "nobody", "X", 1)

    def test_two_stores_are_independent(self):
        from store.store import Store
        a, b = Store(db.Database()), Store(db.Database())
        a.add_product("A1", "Widget", 10)
        a.add_customer("c1", "Ada")
        a.place_order("o1", "c1", "A1", 1)
        self.assertIsNone(b.get_product("A1"), "state leaked between Store instances")
        self.assertIsNone(b.get_order("o1"), "state leaked between Store instances")
        self.assertEqual(b.sales_report()["orders"], 0)

    def test_store_is_independent_of_the_global(self):
        from store.store import Store
        seed_via_modules()
        s = Store(db.Database())
        self.assertEqual(s.sales_report()["orders"], 0,
                         "Store must not read the module-level CONNECTION")
        s.add_product("Z9", "Zonk", 5)
        self.assertIsNone(products.get_product("Z9"),
                          "Store writes leaked into the global connection")


class TestGlobalNoLongerReachedInto(unittest.TestCase):
    def _sources(self):
        pkg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "store")
        out = {}
        for fn in os.listdir(pkg):
            if fn.endswith(".py"):
                with open(os.path.join(pkg, fn)) as f:
                    out[fn] = f.read()
        return out

    def test_no_direct_connection_access_outside_db(self):
        offenders = []
        for fn, src in self._sources().items():
            if fn in ("db.py", "store.py"):
                continue
            body = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
            if re.search(r"\bCONNECTION\b", body):
                offenders.append(fn)
        self.assertEqual(offenders, [],
                         f"these modules still reach into the global: {offenders}")
