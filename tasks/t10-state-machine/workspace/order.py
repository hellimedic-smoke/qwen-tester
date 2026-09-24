class InvalidTransition(Exception):
    """Raised when a transition is not legal from the current state."""


class Order:
    """An order moving through draft -> paid -> shipped -> delivered.

    See PROMPT.md for the full transition table.
    """

    def __init__(self):
        raise NotImplementedError
