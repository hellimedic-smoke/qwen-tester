#!/usr/bin/env bash
# Validate the suite itself.
#   ./selftest.sh baseline   - tests must FAIL on the untouched workspace
#   ./selftest.sh solutions  - tests must PASS with solutions/ applied
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-baseline}"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
fails=0

for TD in "$ROOT"/tasks/*/; do
  t=$(basename "$TD")
  WS="$TMP/$t"; mkdir -p "$WS"
  cp -r "$TD/workspace/." "$WS/"
  [ "$MODE" = solutions ] && [ -d "$ROOT/solutions/$t" ] && cp -r "$ROOT/solutions/$t/." "$WS/"
  cp "$TD/tests/"_verify_*.py "$WS/" 2>/dev/null
  OUT=$( cd "$WS" && python3 "$ROOT/lib/timeout.py" 180 python3 -m unittest discover -p '_verify_*.py' -v 2>&1 )
  RC=$?
  RAN=$(grep -cE '\.\.\. (ok|FAIL|ERROR|skipped)' <<<"$OUT")
  BAD=$(grep -cE '\.\.\. (FAIL|ERROR)' <<<"$OUT")
  if [ "$MODE" = baseline ]; then
    if [ "$RC" -eq 0 ]; then echo "FAIL $t : passes with no work done"; fails=$((fails+1))
    elif [ "$RAN" -eq 0 ]; then echo "FAIL $t : suite did not run ($(tail -3 <<<"$OUT" | tr '\n' ' '))"; fails=$((fails+1))
    else echo "ok   $t : $BAD/$RAN failing as expected"; fi
  else
    if [ "$RC" -eq 0 ] && [ "$RAN" -gt 0 ]; then echo "ok   $t : $RAN/$RAN passing"
    else echo "FAIL $t : $BAD/$RAN failing"; sed -n '/FAIL:\|ERROR:/,+12p' <<<"$OUT" | head -40; fails=$((fails+1)); fi
  fi
done
echo; [ "$fails" -eq 0 ] && echo "selftest ($MODE): all good" || echo "selftest ($MODE): $fails task(s) wrong"
exit "$fails"
