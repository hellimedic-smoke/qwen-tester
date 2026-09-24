def diff(a, b):
    """Return a minimal edit script turning sequence `a` into sequence `b`.

    Returns a list of (op, value) pairs with op in {"equal", "delete", "insert"}.
    See PROMPT.md for the exact contract.
    """
    raise NotImplementedError
