`pagination.py` powers the paging controls of an internal admin UI. QA filed
three bugs against it:

1. On a result set that divides evenly by the page size (e.g. 20 items, 10 per
   page), the UI shows an extra empty final page.
2. With zero results the UI renders "Page 1 of 0" and the Next button is active.
3. Asking for a page past the end returns items from the last page instead of
   an error.

Fix `paginate(items, page, per_page)` so that:
- `total_pages` is the true number of pages, and is `1` for an empty result set
  (an empty first page, not zero pages)
- `has_next` / `has_prev` are correct on the first, last and only page
- requesting `page < 1` or `page > total_pages` raises `ValueError`
- `per_page < 1` raises `ValueError`
- the returned dict keeps its existing keys and `items` holds that page's slice

`smoke_test.py` covers bug 1. Do not change the function name or signature.
