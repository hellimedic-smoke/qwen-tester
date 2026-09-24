`csvparse.py` contains a hand-rolled CSV reader used by a data import tool. It
splits on commas and newlines naively, so it corrupts any file that uses
quoting. `smoke_test.py` demonstrates one failure.

Fix `parse_csv(text)` so it returns a list of rows (each row a list of string
fields) following normal CSV rules:
- a field wrapped in double quotes may contain commas, newlines, and quotes
- inside a quoted field, `""` means one literal `"` character
- surrounding quotes are stripped; unquoted fields are taken literally
- empty fields and trailing empty fields are preserved
- a trailing newline at the end of the input does not produce an extra row
- a blank line in the middle of the input is a row holding one empty field
  (`[""]`), not skipped
- `\r\n` line endings are treated the same as `\n`
- malformed input (a quoted field that is never closed) raises `ValueError`

This code must not use Python's `csv` module — the import tool needs its own
parser. Do not change the function name or signature.
