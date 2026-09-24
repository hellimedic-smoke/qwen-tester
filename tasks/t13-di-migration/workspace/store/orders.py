from . import db


def place_order(order_id, customer_id, sku, qty):
    product = db.CONNECTION.fetch("products", sku)
    if product is None:
        raise ValueError(f"no such product: {sku}")
    if db.CONNECTION.fetch("customers", customer_id) is None:
        raise ValueError(f"no such customer: {customer_id}")
    if qty < 1:
        raise ValueError("qty must be at least 1")
    total = product["price"] * qty
    db.CONNECTION.insert("orders", order_id, {
        "id": order_id, "customer_id": customer_id, "sku": sku, "qty": qty, "total": total,
    })
    return db.CONNECTION.fetch("orders", order_id)


def get_order(order_id):
    return db.CONNECTION.fetch("orders", order_id)
