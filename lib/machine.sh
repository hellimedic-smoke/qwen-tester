#!/usr/bin/env bash
# Describe this machine.
#   lib/machine.sh        key=value lines (chip, memory_gb, macos, omlx, opencode, date, note)
#   lib/machine.sh slug   short id for directory names, e.g. m5-max-128gb
set -uo pipefail
CHIP=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo unknown)
MEM_GB=$(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 ))
if [ "${1:-}" = slug ]; then
  s=$(echo "$CHIP" | tr '[:upper:]' '[:lower:]' | sed -e 's/^apple //' -e 's/[^a-z0-9]/-/g')
  echo "${s}-${MEM_GB}gb"; exit 0
fi
echo "chip=$CHIP"
echo "memory_gb=$MEM_GB"
echo "macos=$(sw_vers -productVersion 2>/dev/null || echo unknown)"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
probe() { python3 "$HERE/timeout.py" 10 "$@" 2>/dev/null | head -1; }
echo "omlx=$(probe omlx --version || echo unknown)"
echo "opencode=$(probe opencode --version || echo unknown)"
echo "date=$(date +%Y-%m-%d)"
echo "note=${BENCH_NOTE:-}"
