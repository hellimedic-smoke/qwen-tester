import random
import unittest
from textdiff import diff


def lcs_length(a, b):
    """Independent reference used to check minimality."""
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


class DiffCase(unittest.TestCase):
    def check(self, a, b):
        script = diff(list(a), list(b))
        for op, _ in script:
            self.assertIn(op, ("equal", "delete", "insert"), f"bad op {op!r}")
        rebuilt_a = [v for op, v in script if op in ("equal", "delete")]
        rebuilt_b = [v for op, v in script if op in ("equal", "insert")]
        self.assertEqual(rebuilt_a, list(a), "script does not reproduce a")
        self.assertEqual(rebuilt_b, list(b), "script does not reproduce b")
        edits = sum(1 for op, _ in script if op != "equal")
        best = len(a) + len(b) - 2 * lcs_length(list(a), list(b))
        self.assertEqual(edits, best, f"{edits} edits, but {best} is possible")
        return script


class TestCorrectness(DiffCase):
    def test_identical(self):
        s = self.check("abc", "abc")
        self.assertTrue(all(op == "equal" for op, _ in s))

    def test_empty_inputs(self):
        self.check("", "")
        self.check("abc", "")
        self.check("", "abc")

    def test_pure_insert_and_delete(self):
        self.check("ac", "abc")
        self.check("abc", "ac")

    def test_replacement(self):
        self.check("abc", "axc")

    def test_disjoint(self):
        self.check("abc", "xyz")

    def test_repeated_elements(self):
        self.check("aaa", "aa")
        self.check("abab", "baba")
        self.check("aabbaa", "abba")

    def test_classic_cases(self):
        self.check("kitten", "sitting")
        self.check("ABCABBA", "CBABAC")
        self.check("XMJYAUZ", "MZJAWXU")

    def test_works_on_lists_of_strings(self):
        self.check(["import os", "", "def f():", "    pass"],
                   ["import os", "import sys", "", "def f():", "    return 1"])

    def test_tie_break_delete_before_insert(self):
        s = diff(list("a"), list("b"))
        ops = [op for op, _ in s]
        self.assertEqual(ops, ["delete", "insert"])

    def test_randomized_minimality(self):
        rng = random.Random(99)
        for _ in range(40):
            a = [rng.choice("abcd") for _ in range(rng.randint(0, 25))]
            b = [rng.choice("abcd") for _ in range(rng.randint(0, 25))]
            self.check(a, b)


class TestPerformance(unittest.TestCase):
    DRIVER = r"""
import random, sys
from textdiff import diff
rng = random.Random(7)
a = [rng.randrange(400) for _ in range(1000)]
b = list(a)
for _ in range(120):                       # scatter edits through b
    i = rng.randrange(len(b))
    if rng.random() < 0.5: b[i] = rng.randrange(400)
    else: del b[i]
s = diff(a, b)
assert [v for op, v in s if op in ("equal", "delete")] == a
assert [v for op, v in s if op in ("equal", "insert")] == b
print("ok")
"""

    def test_thousand_elements(self):
        import os, subprocess, sys, tempfile
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "driver.py"), "w") as f:
            f.write(self.DRIVER)
        env = dict(os.environ, PYTHONPATH=os.path.dirname(os.path.abspath(__file__)))
        try:
            p = subprocess.run([sys.executable, "driver.py"], cwd=d, env=env,
                               capture_output=True, text=True, timeout=25)
        except subprocess.TimeoutExpired:
            self.fail("diff of two 1000-element sequences did not finish within 25s")
        self.assertEqual(p.returncode, 0, f"driver failed: {p.stderr[-800:]}")


class TestNoDifflib(unittest.TestCase):
    def test_does_not_use_difflib(self):
        import inspect, re, textdiff
        src = inspect.getsource(textdiff)
        self.assertIsNone(re.search(r"^\s*(import\s+difflib|from\s+difflib)", src, re.M),
                          "must not use difflib")
