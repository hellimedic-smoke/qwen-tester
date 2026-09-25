#!/usr/bin/env bash
# Run every pinned model the server has, then print one combined summary.
#   ./sweep.sh                        all pinned models present on the server
#   ./sweep.sh -o results/<dir>       resume: skip models already finished
#   ./sweep.sh <model-id> ...         an explicit list
# Env: OMLX_URL, BENCH_TIMEOUT, BENCH_NOTE (free text saved in machine.txt)
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PINNED=(
  Qwen3-Coder-30B-A3B-Instruct-MLX-8bit
  Qwen3.8-27B-MLX-8bit
  Qwen3.8-Flash-Next-oQ4e-mtp
)

SWEEP=""
if [ "${1:-}" = "-o" ]; then SWEEP="$2"; shift 2; fi
[ -z "$SWEEP" ] && SWEEP="$ROOT/results/$("$ROOT/lib/machine.sh" slug)-$(date +%Y%m%d-%H%M%S)"

OMLX_URL=$("$ROOT/lib/omlx_url.sh") || { echo "!! no oMLX server at ${OMLX_URL:-127.0.0.1:8000 or :8100} (is it running? try: omlx start)" >&2; exit 2; }
export OMLX_URL
AVAILABLE=$("$ROOT/lib/models.sh" "$OMLX_URL") || { echo "!! no oMLX server at $OMLX_URL" >&2; exit 2; }

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
echo "sweep -> ${SWEEP#"$ROOT/"}"
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
  RC=$?
  if [ "$RC" -eq 130 ]; then
    echo "!! sweep interrupted (resume with: ./sweep.sh -o ${SWEEP#"$ROOT/"})" >&2
    exit 130
  fi
  if [ "$RC" -eq 2 ]; then
    echo "!! $m: setup problem, stopping the sweep (fix it and resume with: ./sweep.sh -o ${SWEEP#"$ROOT/"})" >&2
    exit 2
  fi
  echo
done
ELAPSED=$(( $(date +%s) - START ))
echo "================================================================"
echo "sweep finished in $((ELAPSED/3600))h$(( (ELAPSED%3600)/60 ))m"
echo "================================================================"
"$ROOT/score.sh" "${DIRS[@]}" | tee "$SWEEP/summary.txt"
echo "saved: ${SWEEP#"$ROOT/"}/summary.txt"
