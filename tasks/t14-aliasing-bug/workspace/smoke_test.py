import inventory

assert inventory.generate_report()["total"] == 390.0

first = inventory.apply_discount("A1", 50)["price"]
assert first == 50.0, first

second = inventory.apply_discount("A1", 50)["price"]
assert second == 50.0, f"discount compounded: expected 50.0, got {second}"
print("smoke tests passed")
