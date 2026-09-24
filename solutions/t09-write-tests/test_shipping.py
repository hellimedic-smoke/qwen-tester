import unittest
import shipping
from shipping import shipping_cost


class TestFreeShipping(unittest.TestCase):
    def test_exactly_at_threshold_is_free(self):
        self.assertEqual(shipping_cost(50.00, 2.0), 0.0)

    def test_above_threshold_is_free(self):
        self.assertEqual(shipping_cost(75.00, 2.0), 0.0)

    def test_just_below_threshold_is_not_free(self):
        self.assertEqual(shipping_cost(49.99, 2.0), round(4.99 + 1.25 * 2.0, 2))


class TestRates(unittest.TestCase):
    def test_standard_rate_composition(self):
        self.assertEqual(shipping_cost(10.00, 1.0), 6.24)

    def test_per_kg_rate_scales(self):
        light = shipping_cost(10.00, 1.0)
        heavy = shipping_cost(10.00, 3.0)
        self.assertAlmostEqual(heavy - light, 1.25 * 2.0, places=2)

    def test_rounds_to_two_decimals(self):
        cost = shipping_cost(10.00, 1.0)
        self.assertEqual(cost, 6.24)
        self.assertNotEqual(cost, round(cost, 1))


class TestExpress(unittest.TestCase):
    def test_express_doubles_standard(self):
        self.assertEqual(shipping_cost(10.00, 2.0, express=True),
                         round((4.99 + 1.25 * 2.0) * 2.0, 2))

    def test_express_never_free_above_threshold(self):
        self.assertGreater(shipping_cost(100.00, 2.0, express=True), 0.0)

    def test_express_at_threshold_still_charges(self):
        self.assertGreater(shipping_cost(50.00, 1.0, express=True), 0.0)


class TestValidation(unittest.TestCase):
    def test_zero_weight_rejected(self):
        with self.assertRaises(ValueError):
            shipping_cost(10.00, 0)

    def test_negative_weight_rejected(self):
        with self.assertRaises(ValueError):
            shipping_cost(10.00, -1.0)

    def test_small_negative_subtotal_rejected(self):
        with self.assertRaises(ValueError):
            shipping_cost(-0.50, 1.0)

    def test_zero_subtotal_allowed(self):
        self.assertEqual(shipping_cost(0.0, 1.0), 6.24)


class TestConstants(unittest.TestCase):
    def test_constants_unchanged(self):
        self.assertEqual(shipping.PER_KG, 1.25)
        self.assertEqual(shipping.BASE_RATE, 4.99)
        self.assertEqual(shipping.EXPRESS_MULTIPLIER, 2.0)
        self.assertEqual(shipping.FREE_SHIPPING_THRESHOLD, 50.00)
