#!/usr/bin/env bash
# Print the oMLX server URL: $OMLX_URL if set, else the first of
# http://127.0.0.1:8000 (oMLX's default) and http://127.0.0.1:8100 that answers.
# Exits 1 if none does.
set -uo pipefail
if [ -n "${OMLX_URL:-}" ]; then
  curl -sf --max-time 5 "$OMLX_URL/v1/models" >/dev/null && { echo "$OMLX_URL"; exit 0; }
  exit 1
fi
for u in http://127.0.0.1:8000 http://127.0.0.1:8100; do
  curl -sf --max-time 5 "$u/v1/models" >/dev/null && { echo "$u"; exit 0; }
done
exit 1
