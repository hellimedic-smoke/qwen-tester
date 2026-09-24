`api/orders.py` exposes `list_orders()`, which returns every order in one
response. The collection has grown and it now needs pagination.

Add pagination to `list_orders`, consistent with how the rest of this API
already does it. A client that knows how to page through one collection in this
API should be able to page through orders without learning anything new —
same parameters, same response shape, same limits, same error behaviour.

Do not modify `api/users.py`; it is the reference implementation and other
teams depend on it as it stands.
