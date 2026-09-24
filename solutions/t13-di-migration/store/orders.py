from .store import default_store


def place_order(order_id, customer_id, sku, qty):
    return default_store().place_order(order_id, customer_id, sku, qty)


def get_order(order_id):
    return default_store().get_order(order_id)
