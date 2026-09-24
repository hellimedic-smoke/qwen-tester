The `store` package keeps its database handle in a module-level global,
`db.CONNECTION`, which every other module reaches into directly. This makes the
package impossible to test in isolation and impossible to use against two
databases in one process.

Migrate it to dependency injection:
- Introduce a `Store` class (in `store/store.py`) that is constructed with a
  `Database` and exposes the package's operations as methods:
  `add_product`, `get_product`, `place_order`, `get_order`, `add_customer`,
  `customer_orders`, and `sales_report`.
- The per-domain modules must take the database explicitly rather than reading
  the global.
- Two `Store` instances built on two different `Database` objects must be
  fully independent — nothing may leak between them.
- Existing callers use the module-level functions (`products.add_product(...)`
  and friends) and must keep working exactly as they do today, against the
  global connection. Keep those functions as a thin compatibility layer.

`store/db.py` may still define the global, and the new `store/store.py` may
resolve it in one place for the compatibility layer. No other module may read
`db.CONNECTION` at all.
