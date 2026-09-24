from duration import parse_duration

assert parse_duration("1h30m") == 5400
assert parse_duration(" 1h 30m ") == 5400, "whitespace should be tolerated"
try:
    parse_duration("90")
except ValueError:
    pass
else:
    raise AssertionError("a bare number should raise ValueError")
print("smoke tests passed")
