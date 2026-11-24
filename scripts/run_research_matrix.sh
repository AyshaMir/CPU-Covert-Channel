#!/usr/bin/env bash
# Research-oriented matrix: workloads + full channel grid (slots × interference × affinity).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
chmod +x scripts/*.sh 2>/dev/null || true
sed -i 's/\r$//' scripts/*.sh experiments/*.py 2>/dev/null || true

./scripts/build.sh
./scripts/capture_topology.sh
./scripts/collect_prabha_controls.sh || true

echo "=== Workload under interference (all levels) ==="
python3 experiments/run_experiments.py --fresh --samples 20 --trials 3 \
    --levels none,low,medium,high

echo "=== Channel: same CPU, slots 50/100/200, all interference levels ==="
python3 experiments/run_channel_experiments.py --fresh \
    --message 10101010 \
    --durations 50,100,200 \
    --levels none,low,medium,high \
    --trials 2 \
    --affinity same \
    --cpu 0 \
    --lead-ms 5000

echo "=== Channel: separate CPUs (0 sender / 2 receiver), 100+200 ms ==="
python3 experiments/run_channel_experiments.py \
    --message 10101010 \
    --durations 100,200 \
    --levels none,low,medium,high \
    --trials 2 \
    --affinity separate \
    --cpu 0 \
    --receiver-cpu 2 \
    --lead-ms 5000

echo "=== No-sender control (same CPU) ==="
python3 experiments/run_channel_experiments.py \
    --no-sender \
    --message 10101010 \
    --durations 100 \
    --levels none,high \
    --trials 1 \
    --affinity same \
    --cpu 0

python3 experiments/analyze_results.py
python3 experiments/analyze_results.py --skip-workload --channel-csv results/channel_trials.csv

echo "Research matrix complete. See results/ and docs/KARIM_RESULTS.md"