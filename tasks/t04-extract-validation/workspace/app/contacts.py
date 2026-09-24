import re

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def add_contact(name, email, phone):
    if not EMAIL_PATTERN.match(email or ""):
        raise ValueError("invalid email")
    digits = "".join(c for c in (phone or "") if c.isdigit())
    if len(digits) != 10:
        raise ValueError("invalid phone")
    return {"name": name, "email": email.lower(), "phone": digits}
