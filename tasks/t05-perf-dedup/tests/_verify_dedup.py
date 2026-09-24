import random
import time
import unittest
from dedup import dedup_preserving_order, first_duplicate


class TestCorrectness(unittest.TestCase):
    def test_dedup_order(self):
        self.assertEqual(dedup_preserving_order([3, 1, 3, 2, 1]), [3, 1, 2])

    def test_dedup_empty_and_unique(self):
        self.assertEqual(dedup_preserving_order([]), [])
        self.assertEqual(dedup_preserving_order([1, 2, 3]), [1, 2, 3])

    def test_dedup_mixed_types(self):
        self.assertEqual(dedup_preserving_order(["a", "b", "a", None, None]), ["a", "b", None])

    def test_dedup_accepts_iterator(self):
        self.assertEqual(dedup_preserving_order(iter([1, 1, 2])), [1, 2])

    def test_first_duplicate(self):
        self.assertEqual(first_duplicate([1, 2, 3, 2, 1]), 2)
        self.assertEqual(first_duplicate(["x", "y", "x"]), "x")

    def test_first_duplicate_none(self):
        self.assertIsNone(first_duplicate([]))
        self.assertIsNone(first_duplicate([1, 2, 3]))

    def test_first_duplicate_is_earliest_second_occurrence(self):
        # 5 appears twice but its repeat is later than 9's repeat.
        self.assertEqual(first_duplicate([5, 9, 9, 5]), 9)


class TestPerformance(unittest.TestCase):
    """Run the candidate in a subprocess with a hard wall-clock cap.

    A quadratic implementation blows the cap and fails fast, instead of
    hanging the grading run for minutes.
    """

    DRIVER = r"""
import random, sys
from dedup import dedup_preserving_order, first_duplicate
random.seed(1234)
which = sys.argv[1]
if which == "dedup":
    data = [random.randrange(50_000) for _ in range(200_000)]
    out = dedup_preserving_order(data)
    assert len(out) == len(set(data)), "wrong result"
    assert out[:3] == list(dict.fromkeys(data))[:3], "wrong order"
else:
    data = list(range(200_000))
    data.append(data[0])          # sole duplicate, right at the end
    assert first_duplicate(data) == 0, "wrong result"
print("ok")
"""

    def _run(self, which, cap=10):
        import os, subprocess, sys, tempfile
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "driver.py"), "w") as f:
            f.write(self.DRIVER)
        env = dict(os.environ, PYTHONPATH=os.path.dirname(os.path.abspath(__file__)))
        try:
            proc = subprocess.run([sys.executable, "driver.py", which], cwd=d, env=env,
                                  capture_output=True, text=True, timeout=cap)
        except subprocess.TimeoutExpired:
            self.fail(f"{which} on 200k items did not finish within {cap}s - still quadratic")
        self.assertEqual(proc.returncode, 0, f"{which} failed: {proc.stderr[-800:]}")

    def test_dedup_is_fast(self):
        self._run("dedup")

    def test_first_duplicate_is_fast(self):
        self._run("first_duplicate")
