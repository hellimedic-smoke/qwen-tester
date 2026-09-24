from ._data import USERS
from .errors import ApiError
from .pagination import clamp_limit, decode_cursor, encode_cursor


def list_users(limit=None, cursor=None):
    """Return a page of users ordered by id.

    Paging is keyset-based: `cursor` is an opaque marker for the last id the
    client saw, so inserts and deletes elsewhere in the collection cannot make
    a client skip or repeat a row mid-traversal.
    """
    limit = clamp_limit(limit)
    rows = sorted(USERS, key=lambda r: r["id"])

    if cursor is not None:
        last_id = decode_cursor(cursor)
        if not any(r["id"] == last_id for r in rows):
            raise ApiError("invalid_cursor", "cursor refers to a row that no longer exists")
        rows = [r for r in rows if r["id"] > last_id]

    page = rows[:limit]
    next_cursor = encode_cursor(page[-1]["id"]) if len(rows) > limit else None
    return {"items": page, "next_cursor": next_cursor}
