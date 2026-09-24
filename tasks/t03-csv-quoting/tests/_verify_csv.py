import unittest
from csvparse import parse_csv


class TestParseCSV(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(parse_csv("a,b,c\n1,2,3"), [["a", "b", "c"], ["1", "2", "3"]])

    def test_quoted_comma(self):
        self.assertEqual(parse_csv('"Smith, John",42'), [["Smith, John", "42"]])

    def test_escaped_quote(self):
        self.assertEqual(parse_csv('"she said ""hi""",x'), [['she said "hi"', "x"]])

    def test_embedded_newline(self):
        self.assertEqual(parse_csv('"line1\nline2",b'), [["line1\nline2", "b"]])

    def test_empty_fields(self):
        self.assertEqual(parse_csv("a,,c"), [["a", "", "c"]])
        self.assertEqual(parse_csv("a,b,"), [["a", "b", ""]])
        self.assertEqual(parse_csv(",,"), [["", "", ""]])

    def test_quoted_empty_field(self):
        self.assertEqual(parse_csv('a,"",c'), [["a", "", "c"]])

    def test_trailing_newline_no_extra_row(self):
        self.assertEqual(parse_csv("a,b\n"), [["a", "b"]])

    def test_blank_line_is_a_row(self):
        self.assertEqual(parse_csv("a,b\n\nc,d"), [["a", "b"], [""], ["c", "d"]])

    def test_crlf(self):
        self.assertEqual(parse_csv("a,b\r\nc,d"), [["a", "b"], ["c", "d"]])

    def test_unterminated_quote_raises(self):
        with self.assertRaises(ValueError):
            parse_csv('"never closed,a,b')

    def test_does_not_use_csv_module(self):
        import csvparse, inspect, re
        src = inspect.getsource(csvparse)
        self.assertIsNone(
            re.search(r"^\s*(import\s+csv|from\s+csv\s+import)", src, re.M),
            "must not use the stdlib csv module",
        )
