from .validators import is_valid_email, normalize_phone


def set_billing_contact(account_id, email, phone):
    if not is_valid_email(email):
        raise ValueError("invalid email")
    return {"account_id": account_id, "email": email.lower(), "phone": normalize_phone(phone)}
