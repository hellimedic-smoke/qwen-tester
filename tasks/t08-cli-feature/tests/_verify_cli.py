import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TODO = os.path.join(HERE, "todo.py")


class CLITest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.file = os.path.join(self.dir, "todo.json")

    def run_cli(self, *args, expect_ok=True):
        proc = subprocess.run(
            [sys.executable, TODO, "--file", self.file, *args],
            capture_output=True, text=True, timeout=30,
        )
        if expect_ok:
            self.assertEqual(proc.returncode, 0, f"exit {proc.returncode}: {proc.stderr}")
        return proc

    def seed(self):
        self.run_cli("add", "write tests")
        self.run_cli("add", "fix bug")
        self.run_cli("add", "ship it")
        self.run_cli("done", "2")


class TestExistingBehaviourUnchanged(CLITest):
    def test_add_human_output(self):
        out = self.run_cli("add", "hello").stdout.strip()
        self.assertEqual(out, "added #1: hello")

    def test_list_human_output(self):
        self.seed()
        out = self.run_cli("list").stdout.strip().splitlines()
        self.assertEqual(out[0], "[ ] #1 write tests")
        self.assertEqual(out[1], "[x] #2 fix bug")

    def test_empty_list_human_output(self):
        self.assertEqual(self.run_cli("list").stdout.strip(), "no tasks")

    def test_done_human_output(self):
        self.run_cli("add", "a")
        self.assertEqual(self.run_cli("done", "1").stdout.strip(), "completed #1: a")

    def test_missing_task_still_errors(self):
        proc = self.run_cli("done", "99", expect_ok=False)
        self.assertNotEqual(proc.returncode, 0)


class TestJSONFlag(CLITest):
    def test_add_json(self):
        obj = json.loads(self.run_cli("--json", "add", "hello").stdout)
        self.assertEqual(obj, {"id": 1, "text": "hello", "done": False})

    def test_list_json(self):
        self.seed()
        arr = json.loads(self.run_cli("--json", "list").stdout)
        self.assertEqual(len(arr), 3)
        self.assertEqual(arr[1], {"id": 2, "text": "fix bug", "done": True})

    def test_empty_list_json(self):
        self.assertEqual(json.loads(self.run_cli("--json", "list").stdout), [])

    def test_done_json(self):
        self.run_cli("add", "a")
        obj = json.loads(self.run_cli("--json", "done", "1").stdout)
        self.assertEqual(obj, {"id": 1, "text": "a", "done": True})

    def test_flag_after_subcommand(self):
        self.run_cli("add", "a")
        arr = json.loads(self.run_cli("list", "--json").stdout)
        self.assertEqual(len(arr), 1)


class TestStatsSubcommand(CLITest):
    def test_stats_human(self):
        self.seed()
        self.assertEqual(self.run_cli("stats").stdout.strip(), "3 tasks, 1 done, 2 open")

    def test_stats_json(self):
        self.seed()
        self.assertEqual(
            json.loads(self.run_cli("--json", "stats").stdout),
            {"total": 3, "done": 1, "open": 2},
        )

    def test_stats_empty(self):
        self.assertEqual(self.run_cli("stats").stdout.strip(), "0 tasks, 0 done, 0 open")
