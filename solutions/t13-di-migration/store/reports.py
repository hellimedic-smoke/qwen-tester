from .store import default_store


def sales_report():
    return default_store().sales_report()
