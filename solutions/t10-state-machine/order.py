class InvalidTransition(Exception):
    """Raised when a transition is not legal from the current state."""


TRANSITIONS = {
    "pay": {"draft": "paid"},
    "ship": {"paid": "shipped"},
    "deliver": {"shipped": "delivered"},
    "cancel": {"draft": "cancelled", "paid": "cancelled"},
    "refund": {"paid": "cancelled", "shipped": "cancelled", "delivered": "cancelled"},
}


class Order:
    def __init__(self):
        self.state = "draft"
        self.history = ["draft"]

    def can(self, name):
        return self.state in TRANSITIONS.get(name, {})

    def _apply(self, name):
        if not self.can(name):
            raise InvalidTransition(f"cannot {name} an order in state {self.state}")
        self.state = TRANSITIONS[name][self.state]
        self.history.append(self.state)

    def pay(self):
        self._apply("pay")

    def ship(self):
        self._apply("ship")

    def deliver(self):
        self._apply("deliver")

    def cancel(self):
        self._apply("cancel")

    def refund(self):
        self._apply("refund")
