import re

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def is_valid_email(value):
    return bool(EMAIL_RE.match(value or ""))


def normalize_phone(value):
    digits = "".join(c for c in (value or "") if c.isdigit())
    if len(digits) != 10:
        raise ValueError("invalid phone")
    return digits
