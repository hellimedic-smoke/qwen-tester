#!/usr/bin/env bash
# List model ids served by an oMLX server, one per line. Exits 1 if unreachable.
#   lib/models.sh [url]      default: $OMLX_URL or http://localhost:8100
set -uo pipefail
URL="${1:-${OMLX_URL:-http://localhost:8100}}"
BODY=$(curl -sf --max-time 5 "$URL/v1/models") || exit 1
python3 -c '
import json, sys
for m in json.load(sys.stdin).get("data", []):
    print(m.get("id", ""))' <<<"$BODY"
