#!/usr/bin/env bash
# List model ids served by an oMLX server, one per line. Exits 1 if unreachable.
#   lib/models.sh [url]      default: what lib/omlx_url.sh finds
set -uo pipefail
URL="${1:-}"
[ -z "$URL" ] && { URL=$("$(dirname "${BASH_SOURCE[0]}")/omlx_url.sh") || exit 1; }
BODY=$(curl -sf --max-time 5 "$URL/v1/models") || exit 1
python3 -c '
import json, sys
for m in json.load(sys.stdin).get("data", []):
    print(m.get("id", ""))' <<<"$BODY"
