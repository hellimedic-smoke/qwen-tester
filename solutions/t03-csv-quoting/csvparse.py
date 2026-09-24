def parse_csv(text):
    rows, row, field = [], [], []
    in_quotes = False
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field.append('"'); i += 2; continue
                in_quotes = False; i += 1; continue
            field.append(ch); i += 1; continue
        if ch == '"':
            in_quotes = True; i += 1; continue
        if ch == ",":
            row.append("".join(field)); field = []; i += 1; continue
        if ch == "\r" and i + 1 < n and text[i + 1] == "\n":
            row.append("".join(field)); rows.append(row)
            row, field = [], []; i += 2; continue
        if ch in "\r\n":
            row.append("".join(field)); rows.append(row)
            row, field = [], []; i += 1; continue
        field.append(ch); i += 1
    if in_quotes:
        raise ValueError("unterminated quoted field")
    if field or row or (text and text[-1] not in "\r\n"):
        row.append("".join(field)); rows.append(row)
    return rows
