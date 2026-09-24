from . import db


class Store:
    """All store operations, bound to one Database."""

    def __init__(self, database):
        self.db = database

    def add_product(self, sku, name, price):
        if price < 0:
            raise ValueError("price must not be negative")
        self.db.insert("products", sku, {"sku": sku, "name": name, "price": price})
        return self.db.fetch("products", sku)

    def get_product(self, sku):
        return self.db.fetch("products", sku)

    def add_customer(self, customer_id, name):
        self.db.insert("customers", customer_id, {"id": customer_id, "name": name})
        return self.db.fetch("customers", customer_id)

    def customer_orders(self, customer_id):
        return [o for o in self.db.all("orders") if o["customer_id"] == customer_id]

    def place_order(self, order_id, customer_id, sku, qty):
        product = self.db.fetch("products", sku)
        if product is None:
            raise ValueError(f"no such product: {sku}")
        if self.db.fetch("customers", customer_id) is None:
            raise ValueError(f"no such customer: {customer_id}")
        if qty < 1:
            raise ValueError("qty must be at least 1")
        total = product["price"] * qty
        self.db.insert("orders", order_id, {
            "id": order_id, "customer_id": customer_id, "sku": sku, "qty": qty, "total": total,
        })
        return self.db.fetch("orders", order_id)

    def get_order(self, order_id):
        return self.db.fetch("orders", order_id)

    def sales_report(self):
        orders = self.db.all("orders")
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


def default_store():
    """The compatibility layer's single point of contact with the global."""
    return Store(db.CONNECTION)
