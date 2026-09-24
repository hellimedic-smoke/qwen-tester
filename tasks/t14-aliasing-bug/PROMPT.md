Support filed two bugs against the pricing service:

> 1. Applying the same promotion to an item twice compounds it. Running
>    "50% off A1" once gives £50 as expected; running it again gives £25.
> 2. The marketing preview tool reads an item, adjusts a few fields locally to
>    show the customer a mock-up, and discards it — but afterwards the nightly
>    report is wrong, and stays wrong until the service restarts. Nothing in the
>    preview tool writes anything back.

`inventory.py` is the module involved; `smoke_test.py` reproduces bug 1.

Fix both. The contract the fix has to satisfy:
- A discount **persists** — once applied, the nightly report reflects it.
- A discount is **idempotent** and always relative to the item's original
  price, never to an already-discounted one. Applying "50% off" twice leaves
  the item at half its original price, and does not add the `promo` tag twice.
- Reading an item and modifying the returned value must never affect what
  anyone else sees. This holds for nested values too, not just the top level.
- Caching must stay effective: `_load_from_source` is a stand-in for an
  expensive query and must still be called at most once per SKU, however many
  times an item is read or discounted.
- `apply_discount` must keep returning the discounted item to its caller.

Do not change the signatures of `get_item`, `apply_discount` or
`generate_report`.
