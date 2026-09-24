import os
import re
import unittest
from app import signup, contacts, billing


class TestBehaviourPreserved(unittest.TestCase):
    def test_signup_happy_path(self):
        self.assertEqual(
            signup.register("A.User+tag@example.com", "(555) 123-4567"),
            {"email": "a.user+tag@example.com", "phone": "5551234567"},
        )

    def test_contacts_happy_path(self):
        self.assertEqual(
            contacts.add_contact("Bo", "bo@example.com", "555-123-4567"),
            {"name": "Bo", "email": "bo@example.com", "phone": "5551234567"},
        )

    def test_billing_happy_path(self):
        self.assertEqual(
            billing.set_billing_contact(7, "b@example.com", "555.123.4567"),
            {"account_id": 7, "email": "b@example.com", "phone": "5551234567"},
        )

    def test_all_three_reject_bad_email(self):
        for fn in (lambda: signup.register("nope", "5551234567"),
                   lambda: contacts.add_contact("x", "nope", "5551234567"),
                   lambda: billing.set_billing_contact(1, "nope", "5551234567")):
            with self.assertRaises(ValueError):
                fn()

    def test_all_three_reject_short_phone(self):
        for fn in (lambda: signup.register("a@example.com", "123"),
                   lambda: contacts.add_contact("x", "a@example.com", "123"),
                   lambda: billing.set_billing_contact(1, "a@example.com", "123")):
            with self.assertRaises(ValueError):
                fn()


class TestDriftResolved(unittest.TestCase):
    def test_billing_now_accepts_plus_addressing(self):
        out = billing.set_billing_contact(1, "a.user+tag@example.com", "5551234567")
        self.assertEqual(out["email"], "a.user+tag@example.com")

    def test_billing_now_rejects_eleven_digits(self):
        with self.assertRaises(ValueError):
            billing.set_billing_contact(1, "a@example.com", "15551234567")


class TestDuplicationRemoved(unittest.TestCase):
    def _sources(self):
        here = os.path.dirname(os.path.abspath(__file__))
        pkg = os.path.join(here, "app")
        out = {}
        for fn in os.listdir(pkg):
            if fn.endswith(".py"):
                with open(os.path.join(pkg, fn)) as f:
                    out[fn] = f.read()
        return out

    def test_validators_module_exists(self):
        from app import validators
        self.assertTrue(hasattr(validators, "is_valid_email"))
        self.assertTrue(hasattr(validators, "normalize_phone"))

    def test_email_pattern_defined_once(self):
        hits = [fn for fn, src in self._sources().items() if "@[A-Za-z0-9.-]" in src]
        self.assertEqual(hits, ["validators.py"], f"email pattern still duplicated in {hits}")

    def test_phone_digit_logic_defined_once(self):
        hits = [fn for fn, src in self._sources().items()
                if re.search(r"c\.isdigit\(\)|\.isdigit\(\)\s*\)", src)]
        self.assertEqual(hits, ["validators.py"], f"phone logic still duplicated in {hits}")
