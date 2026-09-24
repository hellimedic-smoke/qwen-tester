from .store import default_store


def add_customer(customer_id, name):
    return default_store().add_customer(customer_id, name)


def customer_orders(customer_id):
    return default_store().customer_orders(customer_id)
