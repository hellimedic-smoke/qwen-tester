import re


def set_billing_contact(account_id, email, phone):
    # NOTE: this copy drifted - it rejects '+' in the local part and allows
    # 11-digit numbers. signup.py is the copy we consider correct.
    if not re.match(r"^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email or ""):
        raise ValueError("invalid email")
    digits = "".join(c for c in (phone or "") if c.isdigit())
    if len(digits) not in (10, 11):
        raise ValueError("invalid phone")
    return {"account_id": account_id, "email": email.lower(), "phone": digits}
