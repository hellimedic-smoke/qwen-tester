def diff(a, b):
    """Minimal edit script via an LCS table, walked forward.

    dp[i][j] is the LCS length of a[i:] and b[j:], so the walk can always pick
    the move that keeps the remaining LCS longest. Ties prefer deletions.
    """
    a, b = list(a), list(b)
    n, m = len(a), len(b)

    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        row, nxt = dp[i], dp[i + 1]
        ai = a[i]
        for j in range(m - 1, -1, -1):
            row[j] = nxt[j + 1] + 1 if ai == b[j] else max(nxt[j], row[j + 1])

    out = []
    i = j = 0
    while i < n and j < m:
        if a[i] == b[j]:
            out.append(("equal", a[i])); i += 1; j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            out.append(("delete", a[i])); i += 1
        else:
            out.append(("insert", b[j])); j += 1
    out.extend(("delete", x) for x in a[i:])
    out.extend(("insert", y) for y in b[j:])
    return out
