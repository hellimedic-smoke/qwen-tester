from . import db


def sales_report():
    orders = db.CONNECTION.all("orders")
    by_sku = {}
    for o in orders:
        entry = by_sku.setdefault(o["sku"], {"sku": o["sku"], "units": 0, "revenue": 0})
        entry["units"] += o["qty"]
        entry["revenue"] += o["total"]
    return {
        "orders": len(orders),
        "revenue": sum(o["total"] for o in orders),
        "by_sku": sorted(by_sku.values(), key=lambda e: e["sku"]),
    }
