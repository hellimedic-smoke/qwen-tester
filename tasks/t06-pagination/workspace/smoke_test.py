from pagination import paginate

r = paginate(list(range(20)), 1, 10)
assert r["total_pages"] == 2, f"20 items / 10 per page is 2 pages, got {r['total_pages']}"
print("smoke tests passed")
