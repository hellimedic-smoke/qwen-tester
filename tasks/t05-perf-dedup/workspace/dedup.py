def dedup_preserving_order(items):
    """Return items with duplicates removed, keeping first occurrence order."""
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def first_duplicate(items):
    """Return the first item that appears more than once, else None."""
    items = list(items)
    for i, item in enumerate(items):
        if items.index(item) != i:
            return item
    return None
