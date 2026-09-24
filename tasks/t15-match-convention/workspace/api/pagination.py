"""Cursor helpers shared by paginated endpoints."""
import base64

from .errors import ApiError

DEFAULT_LIMIT = 25
MAX_LIMIT = 100


def encode_cursor(value):
    return base64.urlsafe_b64encode(str(value).encode()).decode().rstrip("=")


def decode_cursor(cursor):
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        return base64.urlsafe_b64decode(padded.encode()).decode()
    except Exception:
        raise ApiError("invalid_cursor", "cursor is not valid")


def clamp_limit(limit):
    if limit is None:
        return DEFAULT_LIMIT
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ApiError("invalid_limit", "limit must be a positive integer")
    return min(limit, MAX_LIMIT)
