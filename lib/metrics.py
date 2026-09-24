"""Extract output tokens and turn count from an opencode JSON transcript."""
import json
import sys


def opencode(path):
    out = turns = 0
    with open(path) as f:
        for line in f:
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("type") != "step_finish":
                continue
            part = o.get("part") or {}
            out += (part.get("tokens") or {}).get("output") or 0
            turns += 1
    return out, turns


if __name__ == "__main__":
    try:
        o, t = opencode(sys.argv[1])
    except Exception:
        o, t = 0, 0
    print(f"{o} {t}")
