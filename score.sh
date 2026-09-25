#!/usr/bin/env bash
# Summarize one or more model runs side by side.
#   ./score.sh results/<sweep>/*/
#   ./score.sh results/<sweep-a>/*/ results/<sweep-b>/*/
set -uo pipefail
[ $# -lt 1 ] && { echo "usage: ./score.sh <run-dir> [run-dir ...]" >&2; exit 2; }

python3 - "$@" <<'PY'
import csv, os, sys

def short(model):
    for junk in ("-MLX", "-mlx", "-Instruct", "Qwen", "-oQ4e-mtp"):
        model = model.replace(junk, "")
    return model.strip("-.")[:10]

def machine(run):
    p = os.path.join(os.path.dirname(run.rstrip("/")), "machine.txt")
    if not os.path.exists(p):
        return None
    kv = dict(l.rstrip("\n").split("=", 1) for l in open(p) if "=" in l)
    return f"{kv.get('chip','?')} {kv.get('memory_gb','?')} GB"

runs, rows, machines = [], {}, {}
for r in sys.argv[1:]:
    tsv = os.path.join(r, "results.tsv")
    if not os.path.exists(tsv):
        print(f"(skipping {r}: no results.tsv)", file=sys.stderr); continue
    cfg = os.path.join(r, "config")
    model = open(cfg).read().strip() if os.path.exists(cfg) else os.path.basename(r.rstrip("/"))
    name = short(model)
    while name in rows:
        name += "'"
    runs.append(name)
    machines[name] = machine(r)
    with open(tsv) as f:
        rows[name] = {x["task"]: x for x in csv.DictReader(f, delimiter="\t")}

if not runs:
    sys.exit("nothing to summarize")

tasks = sorted({t for d in rows.values() for t in d})
W = max([len(t) for t in tasks] + [len("TEST CASES")]) + 2
C = max(max(len(n) for n in runs), 10) + 2
ABBR = {"PASS": "P", "FAIL": "F", "TIMEOUT": "T", "BROKEN": "B"}

def line(cells, first):
    return first.ljust(W) + "".join(str(c).ljust(C)[:C] for c in cells)

print()
if any(machines.values()):
    legend = []
    for n in runs:
        m = machines[n] or "unknown machine"
        if m not in legend:
            legend.append(m)
    for i, m in enumerate(legend, 1):
        print(f"[{i}] {m}")
    print(line([f"[{legend.index(machines[n] or 'unknown machine') + 1}]" for n in runs], "machine"))
print(line(runs, "task") + "solved")
print("-" * (W + C * len(runs) + 6))
for t in tasks:
    cells, solved = [], 0
    for n in runs:
        r = rows[n].get(t)
        if not r:
            cells.append("-"); continue
        st = ABBR.get(r["status"], "?")
        tot = int(r["passed"]) + int(r["failed"])
        cells.append(f"{st} {r['passed']}/{tot}")
        solved += r["status"] == "PASS"
    print(line(cells, t) + f"{solved}/{len(runs)}")
print("-" * (W + C * len(runs) + 6))

def agg(title, fn):
    print(line([fn(rows[n]) for n in runs], title))

def secs(d): return sum(int(r["agent_secs"]) for r in d.values())
def toks(d): return sum(int(r.get("out_tokens") or 0) for r in d.values())

agg("PASSED",     lambda d: f"{sum(1 for r in d.values() if r['status']=='PASS')}/{len(d)}")
agg("TEST CASES", lambda d: "{}/{}".format(
    sum(int(r["passed"]) for r in d.values()),
    sum(int(r["passed"]) + int(r["failed"]) for r in d.values())))
agg("WALL CLOCK", lambda d: "{}m{:02d}s".format(secs(d) // 60, secs(d) % 60))
agg("OUT TOKENS", lambda d: str(toks(d)))
agg("OUT TOK/S",  lambda d: "{:.1f}".format(toks(d) / secs(d) if secs(d) else 0.0))
print()
print("P=pass  F=fail  T=timeout  B=broken (suite could not run)")
print("OUT TOK/S = output tokens / agent wall clock, summed over the run.")
print()
PY
