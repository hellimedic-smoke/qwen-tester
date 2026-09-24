import re

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def register(email, phone):
    if not EMAIL_RE.match(email or ""):
        raise ValueError("invalid email")
    digits = "".join(c for c in (phone or "") if c.isdigit())
    if len(digits) != 10:
        raise ValueError("invalid phone")
    return {"email": email.lower(), "phone": digits}
