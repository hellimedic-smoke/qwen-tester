from .validators import is_valid_email, normalize_phone


def register(email, phone):
    if not is_valid_email(email):
        raise ValueError("invalid email")
    return {"email": email.lower(), "phone": normalize_phone(phone)}
