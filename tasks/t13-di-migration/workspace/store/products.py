from . import db


def add_product(sku, name, price):
    if price < 0:
        raise ValueError("price must not be negative")
    db.CONNECTION.insert("products", sku, {"sku": sku, "name": name, "price": price})
    return db.CONNECTION.fetch("products", sku)


def get_product(sku):
    return db.CONNECTION.fetch("products", sku)
