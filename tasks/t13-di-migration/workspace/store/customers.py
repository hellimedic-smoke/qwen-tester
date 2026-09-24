from . import db


def add_customer(customer_id, name):
    db.CONNECTION.insert("customers", customer_id, {"id": customer_id, "name": name})
    return db.CONNECTION.fetch("customers", customer_id)


def customer_orders(customer_id):
    return [o for o in db.CONNECTION.all("orders") if o["customer_id"] == customer_id]
