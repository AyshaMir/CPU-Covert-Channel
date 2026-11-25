#!/usr/bin/env bash
# Record host CPU topology for report / 8GB vs 16GB comparison (Karim B2).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/results/topology/$(hostname)_cpu_topology.txt}"
mkdir -p "$(dirname "$OUT")"

{
    echo "recorded_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "hostname=$(hostname)"
    echo "nproc=$(nproc 2>/dev/null || echo unknown)"
    echo "----- /proc/cpuinfo (summary) -----"
    if [[ -r /proc/cpuinfo ]]; then
        grep -E '^(processor|model name|cpu cores|siblings|cpu MHz)' /proc/cpuinfo | head -80
    else
        echo "(no /proc/cpuinfo)"
    fi
    echo "----- lscpu -----"
    if command -v lscpu >/dev/null 2>&1; then
        lscpu
    else
        echo "(lscpu not available)"
    fi
} >"$OUT"

echo "Wrote $OUT"