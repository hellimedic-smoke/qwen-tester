import importlib
import unittest


class InventoryCase(unittest.TestCase):
    def setUp(self):
        import inventory
        self.inv = importlib.reload(inventory)


class TestReportedBug(InventoryCase):
    def test_discount_affects_only_that_item(self):
        self.inv.apply_discount("A1", 50)
        report = self.inv.generate_report()
        prices = {i["sku"]: i["price"] for i in report["items"]}
        self.assertEqual(prices["A1"], 50.0)
        self.assertEqual(prices["B2"], 250.0, "an unrelated item's price changed")
        self.assertEqual(prices["C3"], 40.0, "an unrelated item's price changed")
        self.assertEqual(report["total"], 340.0)

    def test_discount_does_not_compound(self):
        first = self.inv.apply_discount("A1", 50)["price"]
        second = self.inv.apply_discount("A1", 50)["price"]
        self.assertEqual(first, 50.0)
        self.assertEqual(second, 50.0, "applying the same discount twice compounded it")

    def test_discount_is_relative_to_original_price(self):
        self.inv.apply_discount("A1", 50)
        self.assertEqual(self.inv.apply_discount("A1", 10)["price"], 90.0,
                         "a later discount must apply to the original price")

    def test_promo_tag_not_duplicated(self):
        self.inv.apply_discount("B2", 20)
        item = self.inv.apply_discount("B2", 20)
        self.assertEqual(item["meta"]["tags"].count("promo"), 1,
                         "promo tag added twice")

    def test_discount_persists_in_report(self):
        self.inv.apply_discount("A1", 50)
        prices = {i["sku"]: i["price"] for i in self.inv.generate_report()["items"]}
        self.assertEqual(prices["A1"], 50.0, "discount did not persist")

    def test_report_is_stable_across_calls(self):
        a = self.inv.generate_report()
        b = self.inv.generate_report()
        self.assertEqual(a, b)
        self.assertEqual(a["total"], 390.0)

    def test_report_unchanged_by_reading_items(self):
        for _ in range(3):
            self.inv.get_item("A1")
        self.assertEqual(self.inv.generate_report()["total"], 390.0)


class TestCacheIsolation(InventoryCase):
    def test_mutating_returned_item_does_not_corrupt_cache(self):
        item = self.inv.get_item("A1")
        item["price"] = 1.0
        item["name"] = "tampered"
        self.assertEqual(self.inv.get_item("A1")["price"], 100.0)
        self.assertEqual(self.inv.get_item("A1")["name"], "Widget")

    def test_nested_structures_are_isolated(self):
        item = self.inv.get_item("B2")
        item["meta"]["tags"].append("junk")
        item["meta"]["warehouse"] = "nowhere"
        fresh = self.inv.get_item("B2")
        self.assertEqual(fresh["meta"]["tags"], ["hardware", "premium"],
                         "nested list is shared with the cache")
        self.assertEqual(fresh["meta"]["warehouse"], "south")

    def test_two_reads_are_independent_objects(self):
        a = self.inv.get_item("C3")
        b = self.inv.get_item("C3")
        a["price"] = 999.0
        self.assertEqual(b["price"], 40.0)


class TestCachingStillWorks(InventoryCase):
    def test_loads_once_per_sku(self):
        for _ in range(5):
            self.inv.get_item("A1")
            self.inv.get_item("B2")
        self.assertEqual(self.inv.load_count, 2,
                         f"expected 2 source loads, got {self.inv.load_count}")

    def test_report_does_not_reload_each_time(self):
        self.inv.generate_report()
        after_first = self.inv.load_count
        self.inv.generate_report()
        self.assertEqual(self.inv.load_count, after_first, "report reloaded cached items")

    def test_discount_does_not_reload(self):
        self.inv.get_item("A1")
        before = self.inv.load_count
        self.inv.apply_discount("A1", 10)
        self.assertEqual(self.inv.load_count, before)


class TestDiscountContract(InventoryCase):
    def test_returns_discounted_item(self):
        out = self.inv.apply_discount("B2", 20)
        self.assertEqual(out["sku"], "B2")
        self.assertEqual(out["price"], 200.0)

    def test_unknown_sku_still_raises(self):
        with self.assertRaises(KeyError):
            self.inv.get_item("NOPE")
