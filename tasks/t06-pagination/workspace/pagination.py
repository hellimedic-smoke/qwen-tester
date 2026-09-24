def paginate(items, page, per_page):
    """Slice `items` into a page of results for the admin UI."""
    total = len(items)
    total_pages = total // per_page + 1
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }
