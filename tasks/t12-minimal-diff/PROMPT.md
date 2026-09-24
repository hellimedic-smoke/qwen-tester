Implement `diff(a, b)` in `textdiff.py`. It powers the review view of an
internal tool, so the edit script it produces must be **minimal** — reviewers
complain when it reports a whole block as changed where a shorter edit exists.

`diff(a, b)` takes two sequences and returns a list of `(op, value)` pairs where
`op` is `"equal"`, `"delete"` or `"insert"`:
- `"equal"` — the value appears in both, `"delete"` — only in `a`,
  `"insert"` — only in `b`
- taking the `"equal"` and `"delete"` values in order must reproduce `a`
- taking the `"equal"` and `"insert"` values in order must reproduce `b`
- the number of `"delete"` plus `"insert"` pairs must be the **smallest
  possible** for that pair of inputs
- where a tie exists, emit deletions before insertions

It must also be fast enough for review-sized inputs: two sequences of 1,000
elements must diff in a couple of seconds, so an exponential search is not
acceptable.

Do not use `difflib` — its output is not minimal and the tool needs an exact
edit script. Do not change the function name or signature.
