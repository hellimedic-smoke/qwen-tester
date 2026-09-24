"""Score the agent's test suite by how many seeded regressions it catches."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "shipping.py")
SUITE = os.path.join(HERE, "test_shipping.py")

MUTANTS = {
    "threshold_boundary": (
        "subtotal >= FREE_SHIPPING_THRESHOLD",
        "subtotal > FREE_SHIPPING_THRESHOLD",
    ),
    "per_kg_rate": ("PER_KG = 1.25", "PER_KG = 1.50"),
    "express_multiplier": ("cost *= EXPRESS_MULTIPLIER", "cost *= 1.0"),
    "express_bypasses_free_shipping": ("and not express", "or not express"),
    "rounding_precision": ("return round(cost, 2)", "return round(cost, 1)"),
    "zero_weight_validation": ("if weight_kg <= 0", "if weight_kg < 0"),
    "negative_subtotal_validation": ("if subtotal < 0", "if subtotal < -1"),
}


def run_suite(directory):
    """Run the agent's suite in `directory`; return True if it passed."""
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "test_shipping", "-v"],
        cwd=directory, capture_output=True, text=True, timeout=120,
    )
    return proc.returncode == 0, proc.stdout + proc.stderr


class TestSuiteIsUsable(unittest.TestCase):
    def test_suite_file_exists(self):
        self.assertTrue(os.path.exists(SUITE), "test_shipping.py was not created")

    def test_suite_passes_on_correct_code(self):
        ok, out = run_suite(HERE)
        self.assertTrue(ok, f"suite must be green against the correct code:\n{out[-2000:]}")


class TestCatchesRegressions(unittest.TestCase):
    """Each test seeds one bug; the agent's suite must notice."""

    def _kills(self, name):
        old, new = MUTANTS[name]
        with open(SRC) as f:
            src = f.read()
        self.assertIn(old, src, f"shipping.py no longer contains {old!r}; it must not be modified")
        tmp = tempfile.mkdtemp()
        try:
            shutil.copy(SUITE, tmp)
            with open(os.path.join(tmp, "shipping.py"), "w") as f:
                f.write(src.replace(old, new, 1))
            ok, out = run_suite(tmp)
            self.assertFalse(ok, f"suite still passed after changing {old!r} -> {new!r}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def _make(name):
    def test(self):
        self._kills(name)
    test.__name__ = f"test_catches_{name}"
    return test


for _n in MUTANTS:
    setattr(TestCatchesRegressions, f"test_catches_{_n}", _make(_n))
