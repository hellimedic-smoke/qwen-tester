def paginate(items, page, per_page):
    if per_page < 1:
        raise ValueError("per_page must be at least 1")
    total = len(items)
    total_pages = max(1, -(-total // per_page))
    if page < 1 or page > total_pages:
        raise ValueError(f"page {page} out of range (1..{total_pages})")
    start = (page - 1) * per_page
    return {
        "items": items[start:start + per_page],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }
