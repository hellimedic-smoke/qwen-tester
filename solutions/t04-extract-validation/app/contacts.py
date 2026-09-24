from .validators import is_valid_email, normalize_phone


def add_contact(name, email, phone):
    if not is_valid_email(email):
        raise ValueError("invalid email")
    return {"name": name, "email": email.lower(), "phone": normalize_phone(phone)}
