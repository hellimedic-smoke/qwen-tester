`dedup.py` provides `dedup_preserving_order(items)` and `first_duplicate(items)`,
used in a data pipeline. They are correct but far too slow: a batch of 200,000
records now takes minutes instead of seconds.

Make both functions fast enough to process 200,000 items in well under a second,
without changing their behaviour:
- `dedup_preserving_order` returns the items with duplicates removed, keeping
  the first occurrence of each, in original order.
- `first_duplicate` returns the first item that appears more than once (the
  element whose *second* occurrence comes earliest), or `None` if there are none.

Items may be any hashable value, and `items` may be any iterable — including a
one-shot iterator, which must not be consumed twice. Do not change the function
names or signatures.
