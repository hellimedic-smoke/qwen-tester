from .store import default_store


def add_product(sku, name, price):
    return default_store().add_product(sku, name, price)


def get_product(sku):
    return default_store().get_product(sku)
