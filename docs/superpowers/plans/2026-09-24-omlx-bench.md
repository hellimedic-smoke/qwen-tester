# omlx-bench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A public repo that runs the 15-task coding benchmark with opencode against three pinned Qwen models on oMLX and prints comparable speed and accuracy tables across Macs.

**Architecture:** Bash scripts drive `opencode run` per task, grade with stdlib `unittest` in a clean process, and write a TSV per model. A shipped `opencode.json` is injected through `OPENCODE_CONFIG`. A machine descriptor and a scorer make results from different Macs comparable.

**Tech Stack:** bash, python3 stdlib, opencode 1.17+, oMLX 0.6+, curl.

**Spec:** `docs/superpowers/specs/2026-09-24-omlx-bench-design.md`

## Global Constraints

- oMLX only. Default server `http://localhost:8100`, override via `OMLX_URL`.
- Three pinned model ids: `Qwen3-Coder-30B-A3B-Instruct-MLX-8bit`, `Qwen3.8-27B-MLX-8bit`, `Qwen3.8-Flash-Next-oQ4e-mtp`.
- `results.tsv` columns: `task status passed failed agent_secs exit out_tokens turns`.
- Result path: `results/<machine-slug>-<YYYYMMDD-HHMMSS>/<model-id>/`.
- Knobs: `BENCH_TIMEOUT` (900), `BENCH_TEST_TIMEOUT` (120), `BENCH_RUN_DIR`, `BENCH_NOTE`.
- No secrets, no `/Users/` or `/home/` paths anywhere in the tree.
- Source harness: `/Users/matthewhelling/omarchy/agent-bench` (referred to below as `$SRC`). Never copy its `results/` transcripts.

## Review Focus

1. Server up but model not loaded: `run.sh` must exit 2 with a one-line message naming the model, not run 15 tasks that all fail. (Task 3 tests this.)
2. `OPENCODE_CONFIG` pointing at a missing file silently falls back to the user's global config. `run.sh` must check the file exists. (Task 3.)
3. Model id containing dots (`Qwen3.8-27B-MLX-8bit`) must survive `curl`/`grep` model discovery and directory naming without globbing. (Task 5 tests discovery with this id.)
4. `score.sh` given a run with zero agent seconds must not divide by zero. (Task 4.)
5. `machine.sh` on a Mac where `omlx` is not on PATH must still print a slug so `run.sh` can name its output directory. (Task 2.)

---

### Task 1: Scaffold from the source harness

**Files:**
- Create: `tasks/` (copy), `solutions/` (copy), `selftest.sh` (copy), `lib/metrics.py`, `.gitignore`

**Interfaces:**
- Produces: `python3 lib/metrics.py <transcript.log>` prints `"<out_tokens> <turns>"`.

- [ ] **Step 1: Copy the task suite and selftest**

```bash
cd ~/omarchy/omlx-bench
SRC=/Users/matthewhelling/omarchy/agent-bench
cp -R "$SRC/tasks" "$SRC/solutions" .
cp "$SRC/selftest.sh" .
find . -name __pycache__ -type d -exec rm -rf {} +
```

- [ ] **Step 2: Run selftest, expect both modes green**

Run: `./selftest.sh baseline && ./selftest.sh solutions`
Expected: last lines `selftest (baseline): all good` and `selftest (solutions): all good`.

- [ ] **Step 3: Write lib/metrics.py (opencode only)**

```python
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
```

- [ ] **Step 4: Test metrics.py against a synthetic transcript**

```bash
printf '%s\n' '{"type":"step_finish","part":{"tokens":{"output":5}}}' 'garbage' '{"type":"text"}' '{"type":"step_finish","part":{"tokens":{"output":7}}}' > /tmp/m.log
python3 lib/metrics.py /tmp/m.log
python3 lib/metrics.py /nonexistent
```
Expected: `12 2` then `0 0`.

- [ ] **Step 5: Write .gitignore**

```
results/**/*.agent.log
results/**/*.test.log
results/**/t[0-9][0-9]-*/
__pycache__/
```

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "Add task suite, solutions, selftest and metrics parser"
```

---

### Task 2: lib/machine.sh

**Files:**
- Create: `lib/machine.sh`

**Interfaces:**
- Produces: `lib/machine.sh` prints key=value lines (`chip, memory_gb, macos, omlx, opencode, date, note`); `lib/machine.sh slug` prints only the slug, e.g. `m5-max-128gb`.

- [ ] **Step 1: Write lib/machine.sh**

```bash
#!/usr/bin/env bash
# Describe this machine. `machine.sh` prints key=value lines; `machine.sh slug` prints a short id.
set -uo pipefail
CHIP=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo unknown)
MEM_GB=$(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 ))
if [ "${1:-}" = slug ]; then
  s=$(echo "$CHIP" | tr '[:upper:]' '[:lower:]' | sed 's/^apple //; s/[^a-z0-9]+/-/g; s/[^a-z0-9]/-/g')
  echo "${s}-${MEM_GB}gb"; exit 0
fi
echo "chip=$CHIP"
echo "memory_gb=$MEM_GB"
echo "macos=$(sw_vers -productVersion 2>/dev/null || echo unknown)"
echo "omlx=$(omlx --version 2>/dev/null | head -1 || echo unknown)"
echo "opencode=$(opencode --version 2>/dev/null | head -1 || echo unknown)"
echo "date=$(date +%Y-%m-%d)"
echo "note=${BENCH_NOTE:-}"
```

- [ ] **Step 2: Test it**

```bash
chmod +x lib/machine.sh
./lib/machine.sh
./lib/machine.sh slug
PATH=/usr/bin:/bin ./lib/machine.sh slug   # omlx and opencode absent
```
Expected: seven key=value lines with `chip=Apple M5 Max`, `memory_gb=128`; slug `m5-max-128gb` both times.

- [ ] **Step 3: Commit**

```bash
git add lib/machine.sh && git commit -m "Add machine descriptor"
```

---

### Task 3: opencode.json and run.sh

**Files:**
- Create: `opencode.json`, `run.sh`

**Interfaces:**
- Consumes: `lib/metrics.py`, `lib/machine.sh slug`.
- Produces: `./run.sh <model-id> [task ...]` writes `$RUN/results.tsv`, `$RUN/config` (the model id), `$RUN/<task>.agent.log`, `$RUN/<task>.test.log`, `$RUN/<task>/` workspace. Exit 2 on preflight failure.

- [ ] **Step 1: Write opencode.json**

```json
{
  "$schema": "https://opencode.ai/config.json",
  "enabled_providers": ["omlx"],
  "provider": {
    "omlx": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "oMLX",
      "options": { "baseURL": "http://localhost:8100/v1" },
      "models": {
        "Qwen3-Coder-30B-A3B-Instruct-MLX-8bit": { "name": "Qwen3-Coder-30B-A3B-Instruct-MLX-8bit", "limit": { "context": 200000, "output": 32000 } },
        "Qwen3.8-27B-MLX-8bit":                  { "name": "Qwen3.8-27B-MLX-8bit",                  "limit": { "context": 200000, "output": 32000 } },
        "Qwen3.8-Flash-Next-oQ4e-mtp":           { "name": "Qwen3.8-Flash-Next-oQ4e-mtp",           "limit": { "context": 200000, "output": 32000 } }
      }
    }
  }
}
```

- [ ] **Step 2: Write run.sh**

```bash
#!/usr/bin/env bash
# Run one model over the task suite.
#   ./run.sh Qwen3-Coder-30B-A3B-Instruct-MLX-8bit              all 15 tasks
#   ./run.sh Qwen3.8-27B-MLX-8bit t02-lru-cache t05-perf-dedup   a subset
# Env: OMLX_URL (default http://localhost:8100)
#      BENCH_TIMEOUT (per-task agent budget, default 900s)
#      BENCH_TEST_TIMEOUT (grading, default 120s)
#      BENCH_RUN_DIR (write results here instead of a fresh dir)
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OMLX_URL="${OMLX_URL:-http://localhost:8100}"
TIMEOUT="${BENCH_TIMEOUT:-900}"
TEST_TIMEOUT="${BENCH_TEST_TIMEOUT:-120}"

MODEL="${1:-}"; shift || true
[ -z "$MODEL" ] && { echo "usage: ./run.sh <model-id> [task...]" >&2; exit 2; }

# ---- preflight -------------------------------------------------------------
die() { echo "!! $*" >&2; exit 2; }
command -v python3 >/dev/null || die "python3 not found"
command -v opencode >/dev/null || die "opencode not found (https://opencode.ai)"
command -v curl >/dev/null || die "curl not found"
[ -f "$ROOT/opencode.json" ] || die "missing $ROOT/opencode.json"
MODELS=$(curl -sf --max-time 5 "$OMLX_URL/v1/models") || die "no oMLX server at $OMLX_URL (is it running? try: omlx start)"
python3 - "$MODEL" <<<"$MODELS" >/dev/null 2>&1 <<'PY' || die "model '$MODEL' is not loaded on $OMLX_URL (see README: models)"
PY
# (the check above is replaced by lib/models.sh in Step 3; keep reading)

# ---- opencode config -------------------------------------------------------
CONFIG="$ROOT/opencode.json"
if [ "$OMLX_URL" != "http://localhost:8100" ]; then
  CONFIG=$(mktemp -t omlx-bench.XXXXXX.json)
  sed "s#http://localhost:8100#$OMLX_URL#" "$ROOT/opencode.json" > "$CONFIG"
  trap 'rm -f "$CONFIG"' EXIT
fi
export OPENCODE_CONFIG="$CONFIG"

TASKS=("$@")
if [ ${#TASKS[@]} -eq 0 ]; then
  mapfile -t TASKS < <(cd "$ROOT/tasks" && ls -d */ | tr -d /)
fi

RUN="${BENCH_RUN_DIR:-$ROOT/results/$("$ROOT/lib/machine.sh" slug)-$(date +%Y%m%d-%H%M%S)/$MODEL}"
mkdir -p "$RUN"
echo "$MODEL" > "$RUN/config"
TSV="$RUN/results.tsv"
printf 'task\tstatus\tpassed\tfailed\tagent_secs\texit\tout_tokens\tturns\n' > "$TSV"

# ---- warm-up: load the model so task 1 is not charged for it --------------
printf '   loading %s ... ' "$MODEL"
W0=$(date +%s)
curl -sf --max-time 600 "$OMLX_URL/v1/chat/completions" -H 'content-type: application/json' \
  -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with the single word: ready\"}],\"max_tokens\":8}" >/dev/null \
  && echo "ready in $(( $(date +%s) - W0 ))s" || echo "warm-up request failed, continuing"

POS=""
[ -n "${BENCH_CONFIG_INDEX:-}" ] && POS="[${BENCH_CONFIG_INDEX}/${BENCH_CONFIG_TOTAL}] "
echo "== ${POS}${MODEL}  -  ${#TASKS[@]} tasks, ${TIMEOUT}s cap each"
CONFIG_START=$(date +%s)

IDX=0
for t in "${TASKS[@]}"; do
  TD="$ROOT/tasks/$t"
  [ -d "$TD" ] || { echo "!! no such task: $t" >&2; continue; }
  WS="$RUN/$t"
  rm -rf "$WS"; mkdir -p "$WS"
  cp -r "$TD/workspace/." "$WS/"
  PROMPT="$(cat "$TD/PROMPT.md")"

  IDX=$((IDX + 1))
  START=$(date +%s)
  timeout "$TIMEOUT" opencode run --auto --dir "$WS" --format json -m "omlx/$MODEL" "$PROMPT" \
    >"$RUN/$t.agent.log" 2>&1
  RC=$?
  AGENT_SECS=$(( $(date +%s) - START ))

  # Grade in a clean process against hidden tests the agent never saw.
  cp "$TD/tests/"_verify_*.py "$WS/" 2>/dev/null
  TESTOUT="$RUN/$t.test.log"
  ( cd "$WS" && timeout "$TEST_TIMEOUT" python3 -m unittest discover -p '_verify_*.py' -v ) >"$TESTOUT" 2>&1
  TRC=$?

  read -r RAN FAILED < <(awk '
    /^Ran [0-9]+ test/ { ran = $2 }
    /^FAILED \(/       { n = 0
                         if (match($0, /failures=[0-9]+/)) n += substr($0, RSTART+9, RLENGTH-9)
                         if (match($0, /errors=[0-9]+/))   n += substr($0, RSTART+7, RLENGTH-7)
                         bad = n }
    END { printf "%d %d\n", ran+0, bad+0 }' "$TESTOUT")
  PASSED=$(( RAN - FAILED ))

  if   [ "$TRC" -eq 0 ] && [ "$RAN" -gt 0 ]; then STATUS=PASS
  elif [ "$RC"  -eq 124 ];                    then STATUS=TIMEOUT
  elif [ "$RAN" -eq 0 ];                      then STATUS=BROKEN
  else                                             STATUS=FAIL; fi

  read -r OUT_TOK TURNS < <(python3 "$ROOT/lib/metrics.py" "$RUN/$t.agent.log")

  MARK=$([ "$STATUS" = PASS ] && echo "OK  " || echo "FAIL")
  MINS=$(awk "BEGIN{printf \"%.1f\", $AGENT_SECS/60}")
  PCT=$(awk "BEGIN{printf \"%d\", ($RAN>0 ? $PASSED*100/$RAN : 0)}")
  TPS=$(awk "BEGIN{printf \"%.1f\", ($AGENT_SECS>0 ? $OUT_TOK/$AGENT_SECS : 0)}")
  printf '   %s %-24s %5s min  %3s%%  (%d/%d cases)  %s tok/s\n' \
    "$MARK" "$t" "$MINS" "$PCT" "$PASSED" "$RAN" "$TPS"

  LEFT=$(( ${#TASKS[@]} - IDX ))
  if [ "$LEFT" -gt 0 ]; then
    NEXT=$(printf '%s, ' "${TASKS[@]:$IDX:3}"); NEXT=${NEXT%, }
    EXTRA=""; [ "$LEFT" -gt 3 ] && EXTRA=", +$((LEFT - 3)) more"
    printf '        %d left: %s%s\n' "$LEFT" "$NEXT" "$EXTRA"
  fi
  printf '%s\t%s\t%d\t%d\t%d\t%d\t%s\t%s\n' \
    "$t" "$STATUS" "$PASSED" "$FAILED" "$AGENT_SECS" "$RC" "$OUT_TOK" "$TURNS" >> "$TSV"
done

CONFIG_SECS=$(( $(date +%s) - CONFIG_START ))
awk -F'\t' -v m="$MODEL" -v secs="$CONFIG_SECS" '
  NR>1 { n++; if ($2=="PASS") p++; cases+=$3; total+=$3+$4; tok+=$7; agent+=$5 }
  END {
    printf "\n   == %s done in %.1f min, %d/%d tasks, %d/%d cases, %.1f out tok/s\n",
      m, secs/60, p, n, cases, total, (agent>0 ? tok/agent : 0)
  }' "$TSV"
```

- [ ] **Step 3: Replace the placeholder model check with lib/models.sh**

Create `lib/models.sh`, which lists model ids on a server, one per line:

```bash
#!/usr/bin/env bash
# List model ids served by an oMLX server. Usage: lib/models.sh [url]
set -uo pipefail
URL="${1:-${OMLX_URL:-http://localhost:8100}}"
curl -sf --max-time 5 "$URL/v1/models" | python3 -c '
import json, sys
for m in json.load(sys.stdin).get("data", []):
    print(m.get("id", ""))'
```

In `run.sh`, replace the two lines from `MODELS=$(curl ...` through `PY` (and the comment after) with:

```bash
MODELS=$("$ROOT/lib/models.sh" "$OMLX_URL") || die "no oMLX server at $OMLX_URL (is it running? try: omlx start)"
grep -qxF "$MODEL" <<<"$MODELS" || die "model '$MODEL' is not on $OMLX_URL (server has: $(tr '\n' ' ' <<<"$MODELS"))"
```

- [ ] **Step 4: Test preflight failures**

```bash
chmod +x run.sh lib/models.sh
./run.sh; echo "rc=$?"
OMLX_URL=http://localhost:1 ./run.sh Qwen3.8-27B-MLX-8bit; echo "rc=$?"
./run.sh not-a-model; echo "rc=$?"
```
Expected: usage line rc=2; `!! no oMLX server at http://localhost:1 ...` rc=2; `!! model 'not-a-model' is not on ...` rc=2. No `results/` directory created in any case.

- [ ] **Step 5: Test one real task**

Run: `BENCH_TIMEOUT=600 ./run.sh Qwen3-Coder-30B-A3B-Instruct-MLX-8bit t01-duration-parse`
Expected: `loading ... ready in Ns`, then one `OK   t01-duration-parse` line with a tok/s figure, and `results/m5-max-128gb-<ts>/Qwen3-Coder-30B-A3B-Instruct-MLX-8bit/results.tsv` with 2 lines, 8 columns.

- [ ] **Step 6: Commit**

```bash
git add opencode.json run.sh lib/models.sh && git commit -m "Add opencode config and single-model runner"
```

---

### Task 4: score.sh

**Files:**
- Create: `score.sh` (adapted from `$SRC/score.sh`)

**Interfaces:**
- Consumes: `<run>/results.tsv`, `<run>/config`, `<run>/../machine.txt`.
- Produces: `./score.sh <run-dir>...` prints a machine header and a table with rows `PASSED`, `TEST CASES`, `WALL CLOCK`, `OUT TOKENS`, `OUT TOK/S`.

- [ ] **Step 1: Write score.sh**

```bash
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
W = max((len(t) for t in tasks), default=10) + 2
C = max(max(len(n) for n in runs), 10) + 2
ABBR = {"PASS": "P", "FAIL": "F", "TIMEOUT": "T", "BROKEN": "B"}

def line(cells, first):
    return first.ljust(W) + "".join(str(c).ljust(C) for c in cells)

print()
if any(machines.values()):
    print(line([machines[n] or "?" for n in runs], "machine"))
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
```

Wide machine names get truncated by the column width; that is acceptable.

- [ ] **Step 2: Test with synthetic runs, including zero seconds**

```bash
chmod +x score.sh
mkdir -p /tmp/sc/a/m1 /tmp/sc/b/m2
printf 'chip=Apple M5 Max\nmemory_gb=128\n' > /tmp/sc/a/machine.txt
printf 'task\tstatus\tpassed\tfailed\tagent_secs\texit\tout_tokens\tturns\nt01\tPASS\t10\t0\t50\t0\t1000\t3\n' > /tmp/sc/a/m1/results.tsv
echo Qwen3.8-27B-MLX-8bit > /tmp/sc/a/m1/config
printf 'task\tstatus\tpassed\tfailed\tagent_secs\texit\tout_tokens\tturns\nt01\tFAIL\t8\t2\t0\t0\t0\t0\n' > /tmp/sc/b/m2/results.tsv
./score.sh /tmp/sc/a/m1 /tmp/sc/b/m2
```
Expected: a `machine` header row with `Apple M5 Max 128 GB` and `?`; columns `3.8-27B-8b` and `m2`; `OUT TOK/S` row `20.0` and `0.0`; no traceback.

- [ ] **Step 3: Commit**

```bash
git add score.sh && git commit -m "Add scorer with tokens-per-second and machine header"
```

---

### Task 5: sweep.sh

**Files:**
- Create: `sweep.sh`

**Interfaces:**
- Consumes: `run.sh`, `score.sh`, `lib/machine.sh`, `lib/models.sh`.
- Produces: `results/<slug>-<ts>/machine.txt`, `<model>/` per model, `summary.txt`.

- [ ] **Step 1: Write sweep.sh**

```bash
#!/usr/bin/env bash
# Run every pinned model that the server has, then print one combined summary.
#   ./sweep.sh                        all pinned models present on the server
#   ./sweep.sh -o results/<dir>       resume: skip models already finished
#   ./sweep.sh <model-id> ...         an explicit list
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OMLX_URL="${OMLX_URL:-http://localhost:8100}"

PINNED=(
  Qwen3-Coder-30B-A3B-Instruct-MLX-8bit
  Qwen3.8-27B-MLX-8bit
  Qwen3.8-Flash-Next-oQ4e-mtp
)

SWEEP=""
if [ "${1:-}" = "-o" ]; then SWEEP="$2"; shift 2; fi
[ -z "$SWEEP" ] && SWEEP="$ROOT/results/$("$ROOT/lib/machine.sh" slug)-$(date +%Y%m%d-%H%M%S)"

AVAILABLE=$("$ROOT/lib/models.sh" "$OMLX_URL") || { echo "!! no oMLX server at $OMLX_URL (try: omlx start)" >&2; exit 2; }

MODELS=("$@")
if [ ${#MODELS[@]} -eq 0 ]; then
  for m in "${PINNED[@]}"; do
    if grep -qxF "$m" <<<"$AVAILABLE"; then MODELS+=("$m")
    else echo "SKIPPED $m  -  not on the server (see README: models)"; fi
  done
fi
[ ${#MODELS[@]} -eq 0 ] && { echo "!! none of the pinned models are on $OMLX_URL" >&2; exit 2; }

mkdir -p "$SWEEP"
[ -f "$SWEEP/machine.txt" ] || "$ROOT/lib/machine.sh" > "$SWEEP/machine.txt"
NTASKS=$(ls -d "$ROOT"/tasks/*/ | wc -l | tr -d ' ')
echo "sweep -> ${SWEEP#$ROOT/}"
echo "${#MODELS[@]} models x $NTASKS tasks"
for m in "${MODELS[@]}"; do echo "   - $m"; done
echo

START=$(date +%s)
DIRS=()
IDX=0
for m in "${MODELS[@]}"; do
  IDX=$((IDX + 1))
  DIR="$SWEEP/$m"
  DIRS+=("$DIR")
  DONE=0
  [ -f "$DIR/results.tsv" ] && DONE=$(( $(wc -l < "$DIR/results.tsv") - 1 ))
  if [ "$DONE" -ge "$NTASKS" ]; then
    echo "== [$IDX/${#MODELS[@]}] $m  -  already complete, skipping"; echo; continue
  fi
  BENCH_RUN_DIR="$DIR" BENCH_CONFIG_INDEX="$IDX" BENCH_CONFIG_TOTAL="${#MODELS[@]}" "$ROOT/run.sh" "$m"
  echo
done
ELAPSED=$(( $(date +%s) - START ))
echo "================================================================"
echo "sweep finished in $((ELAPSED/3600))h$(( (ELAPSED%3600)/60 ))m"
echo "================================================================"
"$ROOT/score.sh" "${DIRS[@]}" | tee "$SWEEP/summary.txt"
echo "saved: ${SWEEP#$ROOT/}/summary.txt"
```

- [ ] **Step 2: Test discovery and skip logic without running tasks**

```bash
chmod +x sweep.sh
./lib/models.sh                                  # lists what the server has
OMLX_URL=http://localhost:1 ./sweep.sh; echo "rc=$?"
```
Expected: model list includes `Qwen3.8-27B-MLX-8bit`; the bad URL gives `!! no oMLX server ...` rc=2.

Then a resume test that touches no model: create a fake complete sweep and confirm every model is skipped and `summary.txt` is produced.

```bash
S=/tmp/fake-sweep; rm -rf $S
for m in Qwen3-Coder-30B-A3B-Instruct-MLX-8bit Qwen3.8-27B-MLX-8bit Qwen3.8-Flash-Next-oQ4e-mtp; do
  mkdir -p "$S/$m"; echo "$m" > "$S/$m/config"
  { printf 'task\tstatus\tpassed\tfailed\tagent_secs\texit\tout_tokens\tturns\n'
    for t in $(ls tasks); do printf '%s\tPASS\t1\t0\t10\t0\t100\t1\n' "$t"; done; } > "$S/$m/results.tsv"
done
./sweep.sh -o $S; ls $S
```
Expected: three `already complete, skipping` lines (or `SKIPPED` for models not on the server, which then are not in the list), a table, and `machine.txt` plus `summary.txt` in `$S`.

- [ ] **Step 3: Commit**

```bash
git add sweep.sh && git commit -m "Add sweep over pinned models with server discovery"
```

---

### Task 6: Seed results

**Files:**
- Create: `results/m5-max-128gb-20260919/machine.txt`, `results/m5-max-128gb-20260919/<model>/results.tsv` and `config` for the three models, `results/m5-max-128gb-20260919/summary.txt`.

- [ ] **Step 1: Copy and reshape the three source TSVs**

```bash
SRC=/Users/matthewhelling/omarchy/agent-bench/results/sweep-20260919-172326
D=results/m5-max-128gb-20260919
for m in Qwen3-Coder-30B-A3B-Instruct-MLX-8bit Qwen3.8-27B-MLX-8bit Qwen3.8-Flash-Next-oQ4e-mtp; do
  mkdir -p "$D/$m"; echo "$m" > "$D/$m/config"
  cut -f1-6,8,9 "$SRC/opencode_omlx_$m/results.tsv" > "$D/$m/results.tsv"
done
cat > "$D/machine.txt" <<'EOF'
chip=Apple M5 Max
memory_gb=128
macos=27.0
omlx=0.6.4
opencode=1.17.14
date=2026-09-19
note=opencode ran inside a Linux VM on this Mac and reached oMLX over the VM NAT; timings include that overhead. BENCH_TIMEOUT was 1200.
EOF
./score.sh "$D"/*/ | tee "$D/summary.txt"
```
Expected: header of each results.tsv is exactly `task status passed failed agent_secs exit out_tokens turns`; table shows 10/15, 13/15, 15/15 passed.

- [ ] **Step 2: Confirm nothing personal came along**

Run: `grep -rn '/home/\|/Users/\|hellimedic' results/`
Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add results && git commit -m "Add seed results from an M5 Max 128 GB"
```

---

### Task 7: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README.md** following the eight sections in the spec. Copy the tasks table and the "Validating the suite" and "Adding a task" sections from `$SRC/README.md` verbatim. Setup instructions:

```
pip install omlx            # or: uv tool install omlx
curl -fsSL https://opencode.ai/install | bash
mkdir -p ~/.omlx/models && cd ~/.omlx/models
hf download lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-8bit --local-dir Qwen3-Coder-30B-A3B-Instruct-MLX-8bit
hf download mlx-community/Qwen3.8-27B-8bit                            --local-dir Qwen3.8-27B-MLX-8bit
hf download Jundot/Qwen3.8-Flash-Next-oQ4e-mtp                        --local-dir Qwen3.8-Flash-Next-oQ4e-mtp
omlx start
./lib/models.sh             # should list the three ids
```

Paste the seed `summary.txt` as the sample table. Include the pinned-models table with disk and minimum memory. Include the contribution flow: run `./sweep.sh`, then commit `results/<slug>-<ts>/` (only machine.txt, summary.txt and results.tsv files are tracked) and open a pull request.

- [ ] **Step 2: Check every command in the README exists in the tree**

Run: `grep -oE '\./[a-z/]+\.sh' README.md | sort -u | while read f; do [ -x "$f" ] && echo "ok $f" || echo "MISSING $f"; done`
Expected: all `ok`.

- [ ] **Step 3: Commit**

```bash
git add README.md && git commit -m "Add README"
```

---

### Task 8: Fresh-clone verification

- [ ] **Step 1: Clone to a temp dir and run selftest**

```bash
T=$(mktemp -d); git clone -q ~/omarchy/omlx-bench "$T/b"; cd "$T/b"
./selftest.sh baseline && ./selftest.sh solutions
```
Expected: both `all good`.

- [ ] **Step 2: Run one real task from the clone**

Run: `BENCH_TIMEOUT=600 ./run.sh Qwen3-Coder-30B-A3B-Instruct-MLX-8bit t07-retry-backoff`
Expected: an `OK` or `FAIL` line with tok/s and a results.tsv; then `git status --short` shows only `results/` entries that are `results.tsv` or `config`, no logs or workspace dirs.

- [ ] **Step 3: Score seed plus fresh run**

Run: `./score.sh results/m5-max-128gb-20260919/*/ results/m5-max-128gb-*/Qwen3-Coder-30B-A3B-Instruct-MLX-8bit/`
Expected: four columns, machine header, `OUT TOK/S` row.

- [ ] **Step 4: Secrets and path sweep on the tracked tree**

```bash
cd ~/omarchy/omlx-bench
git ls-files | xargs grep -nE '(/Users/|/home/|api[_-]?key|sk-[A-Za-z0-9]{20}|ghp_|omlx-[a-z0-9]{16})' | grep -v 'docs/superpowers/plans'
```
Expected: no output. (The plan file names `$SRC`; it is excluded by the filter and is documentation of a one-time copy. Remove the absolute path from the plan before publishing if preferred.)

- [ ] **Step 5: Final commit if anything changed**

```bash
git status --short; git add -A; git commit -m "Verify fresh clone" || true
```
