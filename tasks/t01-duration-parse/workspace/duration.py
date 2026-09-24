UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_duration(s):
    """Parse a duration string like '1h30m' into a total number of seconds."""
    total = 0
    num = ""
    for ch in s:
        if ch.isdigit():
            num += ch
        else:
            total += int(num) * UNITS[ch]
            num = ""
    return total
