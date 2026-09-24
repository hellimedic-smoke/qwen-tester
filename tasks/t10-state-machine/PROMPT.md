Implement the `Order` class in `order.py` as a state machine.

States: `draft`, `paid`, `shipped`, `delivered`, `cancelled`.
A new `Order()` starts in `draft`.

Allowed transitions:
- `pay()`:     draft -> paid
- `ship()`:    paid -> shipped
- `deliver()`: shipped -> delivered
- `cancel()`:  draft -> cancelled, and paid -> cancelled
- `refund()`:  paid -> cancelled, and shipped -> cancelled, and delivered -> cancelled

Rules:
- Any transition that is not listed above raises `InvalidTransition` (already
  defined in the file) with a message naming both the current state and the
  attempted transition.
- `delivered` and `cancelled` are terminal: nothing may leave them, except that
  `refund()` is allowed from `delivered`.
- `order.state` is the current state as a string.
- `order.history` is a list of the states the order has passed through,
  starting with `"draft"` and appending each new state on every successful
  transition.
- `order.can(name)` returns True/False for whether the named transition
  (`"pay"`, `"ship"`, `"deliver"`, `"cancel"`, `"refund"`) is legal right now.

Do not change the class name or the exception name.
