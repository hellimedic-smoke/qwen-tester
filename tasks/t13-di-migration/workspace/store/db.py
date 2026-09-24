class Database:
    """A tiny in-memory stand-in for the real database."""

    def __init__(self):
        self.tables = {"products": {}, "orders": {}, "customers": {}}

    def insert(self, table, key, row):
        self.tables[table][key] = dict(row)

    def fetch(self, table, key):
        row = self.tables[table].get(key)
        return dict(row) if row else None

    def all(self, table):
        return [dict(r) for r in self.tables[table].values()]


CONNECTION = Database()


def reset():
    global CONNECTION
    CONNECTION = Database()
