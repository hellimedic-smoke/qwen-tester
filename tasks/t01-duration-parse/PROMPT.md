`duration.py` has a `parse_duration()` function that converts strings like
`"1h30m"` into a number of seconds. It works for simple inputs but is wrong or
crashes on several real cases. `smoke_test.py` shows two of them.

Fix `parse_duration` so that it:
- supports the units `s`, `m`, `h`, `d`, combined in any order (`"2d4h"`, `"90m"`, `"1h30m15s"`)
- tolerates surrounding and internal whitespace (`" 1h 30m "`)
- raises `ValueError` for anything malformed: empty/whitespace-only input, a
  number with no unit (`"90"`), a unit with no number (`"h"`), unknown units
  (`"5x"`), and negative or non-numeric input

Do not change the function's name or signature. Run `python3 smoke_test.py` to check yourself.
