import re

UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
_TOKEN = re.compile(r"(\d+)([smhd])")


def parse_duration(s):
    if not isinstance(s, str):
        raise ValueError("duration must be a string")
    cleaned = re.sub(r"\s+", "", s)
    if not cleaned:
        raise ValueError("empty duration")
    if not re.fullmatch(r"(?:\d+[smhd])+", cleaned):
        raise ValueError(f"malformed duration: {s!r}")
    return sum(int(n) * UNITS[u] for n, u in _TOKEN.findall(cleaned))
