#!/usr/bin/env bash
# Run one model over the task suite.
#   ./run.sh Qwen3-Coder-30B-A3B-Instruct-MLX-8bit               all 15 tasks
#   ./run.sh Qwen3.8-27B-MLX-8bit t02-lru-cache t05-perf-dedup    a subset
#
# Env: OMLX_URL            oMLX server (default http://localhost:8100)
#      BENCH_TIMEOUT       per-task agent budget in seconds (default 900)
#      BENCH_TEST_TIMEOUT  grading budget in seconds (default 120)
#      BENCH_RUN_DIR       write results here instead of a fresh directory
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OMLX_URL="${OMLX_URL:-http://localhost:8100}"
TIMEOUT="${BENCH_TIMEOUT:-900}"
TEST_TIMEOUT="${BENCH_TEST_TIMEOUT:-120}"
TO="python3 $ROOT/lib/timeout.py"

MODEL="${1:-}"; shift || true
[ -z "$MODEL" ] && { echo "usage: ./run.sh <model-id> [task...]" >&2; exit 2; }

# ---- preflight -------------------------------------------------------------
die() { echo "!! $*" >&2; exit 2; }
command -v python3  >/dev/null || die "python3 not found"
command -v opencode >/dev/null || die "opencode not found (https://opencode.ai)"
command -v curl     >/dev/null || die "curl not found"
[ -f "$ROOT/opencode.json" ] || die "missing $ROOT/opencode.json"
MODELS=$("$ROOT/lib/models.sh" "$OMLX_URL") || die "no oMLX server at $OMLX_URL (is it running? try: omlx start)"
grep -qxF "$MODEL" <<<"$MODELS" || die "model '$MODEL' is not on $OMLX_URL (server has: $(tr '\n' ' ' <<<"$MODELS"))"

# ---- opencode config: ours, never the user's global one --------------------
CONFIG="$ROOT/opencode.json"
if [ "$OMLX_URL" != "http://localhost:8100" ]; then
  CONFIG=$(mktemp -t omlx-bench.XXXXXX)
  sed "s#http://localhost:8100#$OMLX_URL#" "$ROOT/opencode.json" > "$CONFIG"
  trap 'rm -f "$CONFIG"' EXIT
fi
export OPENCODE_CONFIG="$CONFIG"
# Isolate from the user's global opencode config (plugins, providers) and pin
# the version for the duration of the run. The config dir is git-ignored;
# opencode populates it on first use.
mkdir -p "$ROOT/.opencode"
export OPENCODE_CONFIG_DIR="$ROOT/.opencode"
export OPENCODE_DISABLE_AUTOUPDATE=1

TASKS=("$@")
if [ ${#TASKS[@]} -eq 0 ]; then
  while IFS= read -r d; do TASKS+=("$d"); done < <(cd "$ROOT/tasks" && ls -d */ | tr -d /)
fi

RUN="${BENCH_RUN_DIR:-$ROOT/results/$("$ROOT/lib/machine.sh" slug)-$(date +%Y%m%d-%H%M%S)/$MODEL}"
mkdir -p "$RUN"
echo "$MODEL" > "$RUN/config"
TSV="$RUN/results.tsv"
printf 'task\tstatus\tpassed\tfailed\tagent_secs\texit\tout_tokens\tturns\n' > "$TSV"

# ---- warm-up: load the model so the first task is not charged for it ------
printf '   loading %s ... ' "$MODEL"
W0=$(date +%s)
if curl -sf --max-time 600 "$OMLX_URL/v1/chat/completions" -H 'content-type: application/json' \
     -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply with the single word: ready\"}],\"max_tokens\":8}" >/dev/null
then echo "ready in $(( $(date +%s) - W0 ))s"
else echo "warm-up request failed, continuing"; fi

# ---- warm-up: opencode's first call in a checkout must run from the repo
# root, not a workspace subdirectory, or opencode 1.17 hangs before it
# creates its project snapshot. Also proves the config + provider path works.
printf '   checking opencode ... '
W0=$(date +%s)
smoke() { ( cd "$ROOT" && $TO 60 opencode run --auto --format json -m "omlx/$MODEL" "Reply with the single word: ready" </dev/null >/dev/null 2>&1 ); }
if smoke; then echo "ok in $(( $(date +%s) - W0 ))s"
elif { printf 'no reply, retrying ... '; smoke; }; then echo "ok in $(( $(date +%s) - W0 ))s"
else echo "opencode smoke call failed or timed out (see README: troubleshooting), continuing"; fi

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
  cp -R "$TD/workspace/." "$WS/"
  PROMPT="$(cat "$TD/PROMPT.md")"

  IDX=$((IDX + 1))
  START=$(date +%s)
  $TO "$TIMEOUT" opencode run --auto --dir "$WS" --format json -m "omlx/$MODEL" "$PROMPT" \
    <"/dev/null" >"$RUN/$t.agent.log" 2>&1
  RC=$?
  # A timeout with an empty transcript means opencode never started the
  # session (a startup hang, not a slow model). stdin is /dev/null above
  # because `opencode run` reads a non-TTY stdin to the end and waits
  # forever on an open pipe. Retry once from a clean workspace anyway;
  # the clock restarts with the retry.
  if [ "$RC" -eq 124 ] && [ ! -s "$RUN/$t.agent.log" ]; then
    echo "   !!   $t: opencode produced no output in ${TIMEOUT}s, retrying once"
    rm -rf "$WS"; mkdir -p "$WS"; cp -R "$TD/workspace/." "$WS/"
    START=$(date +%s)
    $TO "$TIMEOUT" opencode run --auto --dir "$WS" --format json -m "omlx/$MODEL" "$PROMPT" \
      <"/dev/null" >"$RUN/$t.agent.log" 2>&1
    RC=$?
  fi
  AGENT_SECS=$(( $(date +%s) - START ))

  # Grade in a clean process against hidden tests the agent never saw.
  cp "$TD/tests/"_verify_*.py "$WS/" 2>/dev/null
  TESTOUT="$RUN/$t.test.log"
  ( cd "$WS" && $TO "$TEST_TIMEOUT" python3 -m unittest discover -p '_verify_*.py' -v ) >"$TESTOUT" 2>&1
  TRC=$?

  # Parse unittest's own summary rather than grepping per-test lines, so
  # traceback text can't inflate the counts.
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
