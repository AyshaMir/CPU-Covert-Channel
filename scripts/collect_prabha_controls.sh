#!/usr/bin/env bash
# Run Prabha's affinity/quota scripts in HER worktree (read-only), copy CSVs here.
# Karim does not modify branches/feature-receiver.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PRABHA="$(cd "$ROOT/../branches/feature-receiver" && pwd)"
OUT="$ROOT/results/prabha_controls"
mkdir -p "$OUT"

if [[ ! -d "$PRABHA" ]]; then
    echo "Missing $PRABHA" >&2
    exit 1
fi

cd "$PRABHA"
sed -i 's/\r$//' scripts/affinity.sh scripts/quota.sh 2>/dev/null || true
if [[ ! -x ./bin/benchmark ]]; then
    mkdir -p bin
    gcc -Wall -Wextra -O2 -o bin/benchmark src/benchmark.c -lm
fi

if ! command -v stress-ng >/dev/null 2>&1; then
    echo "WARN: stress-ng not installed; affinity.sh may fail (sudo apt install stress-ng)" >&2
fi

bash scripts/affinity.sh || echo "WARN: affinity.sh failed (see stderr)" >&2
bash scripts/quota.sh || echo "WARN: quota.sh failed (see stderr)" >&2

for f in results/affinity_performance.csv results/quota_performance.csv results/cpu_topology.txt; do
    if [[ -f "$f" ]]; then
        cp -f "$f" "$OUT/$(basename "$f")"
        echo "Copied $(basename "$f") -> $OUT/"
    fi
done

echo "Prabha control baselines (benchmark only) stored under $OUT"