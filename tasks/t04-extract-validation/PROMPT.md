The `app/` package has grown three modules that each re-implement the same
email and phone validation logic by hand: `app/signup.py`, `app/contacts.py`
and `app/billing.py`. The duplication has already caused one bug where the
three copies drifted apart.

Refactor this: create `app/validators.py` holding a single implementation of
`is_valid_email(value)` and `normalize_phone(value)`, and have all three
modules use it instead of their own copies. Each validation rule (the email
pattern and the phone-digit handling) must exist in exactly one place in the
package after your change.

The externally visible behaviour of `signup.register`, `contacts.add_contact`
and `billing.set_billing_contact` must not change — except that any place
where the three copies disagreed should now follow `signup.py`'s behaviour,
which is the correct one.
