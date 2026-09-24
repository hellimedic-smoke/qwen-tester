"""Shipping cost rules for the storefront."""

FREE_SHIPPING_THRESHOLD = 50.00
BASE_RATE = 4.99
PER_KG = 1.25
EXPRESS_MULTIPLIER = 2.0


def shipping_cost(subtotal, weight_kg, express=False):
    """Return the shipping cost for an order, rounded to 2 decimal places.

    Standard orders at or above FREE_SHIPPING_THRESHOLD ship free. Express
    orders always pay, at double the standard rate.
    """
    if subtotal < 0:
        raise ValueError("subtotal must not be negative")
    if weight_kg <= 0:
        raise ValueError("weight must be positive")

    if subtotal >= FREE_SHIPPING_THRESHOLD and not express:
        return 0.0

    cost = BASE_RATE + PER_KG * weight_kg
    if express:
        cost *= EXPRESS_MULTIPLIER
    return round(cost, 2)
