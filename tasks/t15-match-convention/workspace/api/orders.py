from ._data import ORDERS


def list_orders():
    """Return every order, ordered by id."""
    return {"items": sorted(ORDERS, key=lambda r: r["id"])}
