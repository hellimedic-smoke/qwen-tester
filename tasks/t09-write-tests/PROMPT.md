`shipping.py` calculates shipping cost and is currently untested. Write a unit
test suite for it in a new file `test_shipping.py`.

Requirements:
- Use the standard library `unittest` module. It must run green with
  `python3 -m unittest test_shipping` against the current, correct code.
- The suite will be judged on whether it actually catches regressions: your
  tests should fail if someone later changes the free-shipping threshold
  comparison, the per-kg rate, the express multiplier, the rounding, or the
  input validation rules.
- Think about boundary values, not just typical inputs.

Do not modify `shipping.py` — only add the test file.
