USERS = [{"id": f"u-{i:03d}", "name": f"User {i}", "active": i % 7 != 0} for i in range(1, 64)]

ORDERS = [
    {"id": f"o-{i:03d}", "customer": f"u-{(i % 63) + 1:03d}", "total": 10 * i}
    for i in range(1, 58)
]
