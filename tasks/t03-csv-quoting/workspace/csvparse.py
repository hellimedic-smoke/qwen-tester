def parse_csv(text):
    """Parse CSV text into a list of rows, each a list of string fields."""
    rows = []
    for line in text.split("\n"):
        if not line:
            continue
        rows.append(line.split(","))
    return rows
