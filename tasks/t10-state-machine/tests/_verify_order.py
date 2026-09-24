import unittest
from order import Order, InvalidTransition


class TestHappyPath(unittest.TestCase):
    def test_starts_in_draft(self):
        self.assertEqual(Order().state, "draft")

    def test_full_lifecycle(self):
        o = Order()
        o.pay(); self.assertEqual(o.state, "paid")
        o.ship(); self.assertEqual(o.state, "shipped")
        o.deliver(); self.assertEqual(o.state, "delivered")

    def test_cancel_from_draft(self):
        o = Order(); o.cancel()
        self.assertEqual(o.state, "cancelled")

    def test_cancel_from_paid(self):
        o = Order(); o.pay(); o.cancel()
        self.assertEqual(o.state, "cancelled")

    def test_refund_from_shipped_and_delivered(self):
        o = Order(); o.pay(); o.ship(); o.refund()
        self.assertEqual(o.state, "cancelled")
        p = Order(); p.pay(); p.ship(); p.deliver(); p.refund()
        self.assertEqual(p.state, "cancelled")


class TestHistory(unittest.TestCase):
    def test_history_starts_with_draft(self):
        self.assertEqual(Order().history, ["draft"])

    def test_history_records_transitions(self):
        o = Order(); o.pay(); o.ship(); o.deliver()
        self.assertEqual(o.history, ["draft", "paid", "shipped", "delivered"])

    def test_failed_transition_does_not_touch_history(self):
        o = Order()
        with self.assertRaises(InvalidTransition):
            o.ship()
        self.assertEqual(o.history, ["draft"])


class TestIllegalTransitions(unittest.TestCase):
    def test_cannot_skip_payment(self):
        with self.assertRaises(InvalidTransition):
            Order().ship()
        with self.assertRaises(InvalidTransition):
            Order().deliver()

    def test_cannot_pay_twice(self):
        o = Order(); o.pay()
        with self.assertRaises(InvalidTransition):
            o.pay()

    def test_cancelled_is_terminal(self):
        for move in ("pay", "ship", "deliver", "cancel", "refund"):
            o = Order(); o.cancel()
            with self.assertRaises(InvalidTransition, msg=f"{move} from cancelled"):
                getattr(o, move)()

    def test_delivered_is_terminal_except_refund(self):
        for move in ("pay", "ship", "deliver", "cancel"):
            o = Order(); o.pay(); o.ship(); o.deliver()
            with self.assertRaises(InvalidTransition, msg=f"{move} from delivered"):
                getattr(o, move)()

    def test_cannot_refund_a_draft(self):
        with self.assertRaises(InvalidTransition):
            Order().refund()

    def test_error_message_names_state_and_transition(self):
        o = Order()
        with self.assertRaises(InvalidTransition) as ctx:
            o.ship()
        msg = str(ctx.exception).lower()
        self.assertIn("draft", msg)
        self.assertIn("ship", msg)


class TestCan(unittest.TestCase):
    def test_can_in_draft(self):
        o = Order()
        self.assertTrue(o.can("pay"))
        self.assertTrue(o.can("cancel"))
        self.assertFalse(o.can("ship"))
        self.assertFalse(o.can("refund"))

    def test_can_in_paid(self):
        o = Order(); o.pay()
        self.assertTrue(o.can("ship"))
        self.assertTrue(o.can("cancel"))
        self.assertTrue(o.can("refund"))
        self.assertFalse(o.can("pay"))

    def test_can_in_terminal(self):
        o = Order(); o.cancel()
        for move in ("pay", "ship", "deliver", "cancel", "refund"):
            self.assertFalse(o.can(move))
