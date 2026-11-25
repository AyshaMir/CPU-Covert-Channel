#!/usr/bin/env bash
# Research-oriented matrix: workloads + full channel grid (slots × interference × affinity).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# Keep new experiments separate from original datasets
# Give every experiment run a unique output directory.
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)_$$"
RUN_DIR="$ROOT/results/integration_matrix/$RUN_ID"

mkdir -p "$RUN_DIR/plots"

echo "Saving experiment results to: $RUN_DIR"


./scripts/build.sh
./scripts/capture_topology.sh "$RUN_DIR/cpu_topology.txt"
# Prabha's affinity and quota scripts are integrated locally.
# Their experiments are run separately to preserve existing results.
echo "=== Workload under interference (all levels) ==="
python3 experiments/run_experiments.py --samples 20 --trials 3 \
    --levels none,low,medium,high \
    --output "$RUN_DIR/experiment_runs.csv" \
    --raw-output "$RUN_DIR/raw_samples.csv"


echo "=== Channel: same CPU, slots 50/100/200, all interference levels ==="
python3 experiments/run_channel_experiments.py \
    --message 10101010 \
    --durations 50,100,200 \
    --levels none,low,medium,high \
    --trials 2 \
    --affinity same \
    --cpu 0 \
    --lead-ms 5000 \
    --output "$RUN_DIR/channel_trials.csv"

echo "=== Channel: separate CPUs (0 sender / 2 receiver), 100+200 ms ==="
python3 experiments/run_channel_experiments.py \
    --message 10101010 \
    --durations 100,200 \
    --levels none,low,medium,high \
    --trials 2 \
    --affinity separate \
    --cpu 0 \
    --receiver-cpu 2 \
    --lead-ms 5000 \
    --output "$RUN_DIR/channel_trials.csv"

echo "=== No-sender control (same CPU) ==="
python3 experiments/run_channel_experiments.py \
    --no-sender \
    --message 10101010 \
    --durations 100 \
    --levels none,high \
    --trials 1 \
    --affinity same \
    --cpu 0 \
    --output "$RUN_DIR/channel_trials.csv"



echo "=== Analyzing workload results ==="
python3 experiments/analyze_results.py \
    --input "$RUN_DIR/experiment_runs.csv" \
    --raw "$RUN_DIR/raw_samples.csv" \
    --summary "$RUN_DIR/benchmark_slowdown_summary.csv" \
    --plots-dir "$RUN_DIR/plots" \
    --channel-csv "$RUN_DIR/channel_trials.csv" \
    --channel-metrics "$RUN_DIR/channel_metrics.csv" \
    --channel-summary "$RUN_DIR/channel_summary.csv"


echo "Research matrix complete. See results/ and docs/KARIM_RESULTS.md"