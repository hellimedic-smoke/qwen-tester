import unittest
from duration import parse_duration


class TestParseDuration(unittest.TestCase):
    def test_single_units(self):
        self.assertEqual(parse_duration("45s"), 45)
        self.assertEqual(parse_duration("90m"), 5400)
        self.assertEqual(parse_duration("2h"), 7200)
        self.assertEqual(parse_duration("3d"), 259200)

    def test_combined(self):
        self.assertEqual(parse_duration("1h30m"), 5400)
        self.assertEqual(parse_duration("2d4h"), 187200)
        self.assertEqual(parse_duration("1h30m15s"), 5415)

    def test_whitespace(self):
        self.assertEqual(parse_duration(" 1h 30m "), 5400)
        self.assertEqual(parse_duration("1h\t30m"), 5400)

    def test_multi_digit(self):
        self.assertEqual(parse_duration("120m"), 7200)
        self.assertEqual(parse_duration("1000s"), 1000)

    def test_zero(self):
        self.assertEqual(parse_duration("0s"), 0)

    def test_rejects_bare_number(self):
        with self.assertRaises(ValueError):
            parse_duration("90")

    def test_rejects_unit_without_number(self):
        with self.assertRaises(ValueError):
            parse_duration("h")
        with self.assertRaises(ValueError):
            parse_duration("1h m")

    def test_rejects_unknown_unit(self):
        with self.assertRaises(ValueError):
            parse_duration("5x")

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            parse_duration("")
        with self.assertRaises(ValueError):
            parse_duration("   ")

    def test_rejects_negative_and_garbage(self):
        with self.assertRaises(ValueError):
            parse_duration("-5m")
        with self.assertRaises(ValueError):
            parse_duration("abc")
