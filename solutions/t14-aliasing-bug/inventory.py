"""Pricing service: item lookup, promotions and the nightly report."""
import copy

_SOURCE = {
    "A1": {"sku": "A1", "name": "Widget", "price": 100.0,
           "meta": {"tags": ["hardware"], "warehouse": "north"}},
    "B2": {"sku": "B2", "name": "Gadget", "price": 250.0,
           "meta": {"tags": ["hardware", "premium"], "warehouse": "south"}},
    "C3": {"sku": "C3", "name": "Doodad", "price": 40.0,
           "meta": {"tags": ["accessory"], "warehouse": "north"}},
}

_CACHE = {}
_DISCOUNTS = {}
load_count = 0


def _load_from_source(sku):
    """Stand-in for an expensive query. Must not be called twice per sku."""
    global load_count
    load_count += 1
    row = _SOURCE.get(sku)
    if row is None:
        raise KeyError(sku)
    return {"sku": row["sku"], "name": row["name"], "price": row["price"],
            "meta": {"tags": list(row["meta"]["tags"]), "warehouse": row["meta"]["warehouse"]}}


def _base(sku):
    """The canonical cached record. Never handed out, never mutated."""
    if sku not in _CACHE:
        _CACHE[sku] = _load_from_source(sku)
    return _CACHE[sku]


def _effective(sku):
    """A private copy with any standing discount applied to the base price."""
    item = copy.deepcopy(_base(sku))
    percent = _DISCOUNTS.get(sku)
    if percent is not None:
        item["price"] = round(item["price"] * (1 - percent / 100.0), 2)
        if "promo" not in item["meta"]["tags"]:
            item["meta"]["tags"].append("promo")
    return item


def get_item(sku):
    """Return the item record for `sku`, loading it at most once."""
    return _effective(sku)


def apply_discount(sku, percent):
    """Record a standing discount for `sku` and return the discounted item."""
    _base(sku)                      # raises KeyError for an unknown sku
    _DISCOUNTS[sku] = percent
    return _effective(sku)


def generate_report():
    """Total the catalogue at current prices."""
    items = [get_item(sku) for sku in sorted(_SOURCE)]
    return {
        "total": round(sum(i["price"] for i in items), 2),
        "items": [{"sku": i["sku"], "price": i["price"]} for i in items],
    }
