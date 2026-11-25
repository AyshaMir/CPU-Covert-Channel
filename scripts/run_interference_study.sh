
#!/usr/bin/env bash
# Balanced CPU interference study: workloads, covert channel, and controls.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TRIAL_COUNT="${1:-15}"

if ! [[ "$TRIAL_COUNT" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: Trial count must be a positive integer."
    exit 1
fi

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)_$$"
RUN_DIR="$ROOT/results/studies/interference/$RUN_ID"

mkdir -p "$RUN_DIR/plots"

echo "=================================="
echo "CPU Interference Study"
echo "=================================="
echo "Repetitions per condition: $TRIAL_COUNT"
echo "Results: $RUN_DIR"

bash scripts/build.sh
bash scripts/capture_topology.sh "$RUN_DIR/cpu_topology.txt"

# 1. Legitimate workload performance under interference.
echo "=== Workload benchmarking ==="

python3 experiments/run_experiments.py \
    --samples 20 \
    --trials "$TRIAL_COUNT" \
    --levels none,low,medium,high \
    --output "$RUN_DIR/experiment_runs.csv" \
    --raw-output "$RUN_DIR/raw_samples.csv"

# 2. Covert channel on the same logical CPU.
echo "=== Channel: same CPU ==="

python3 experiments/run_channel_experiments.py \
    --message 10101010 \
    --durations 50,100,200 \
    --levels none,low,medium,high \
    --trials "$TRIAL_COUNT" \
    --affinity same \
    --cpu 0 \
    --lead-ms 5000 \
    --output "$RUN_DIR/channel_trials.csv"

# 3. Covert channel on separate logical CPUs.
echo "=== Channel: separate CPUs ==="

python3 experiments/run_channel_experiments.py \
    --message 10101010 \
    --durations 50,100,200 \
    --levels none,low,medium,high \
    --trials "$TRIAL_COUNT" \
    --affinity separate \
    --cpu 0 \
    --receiver-cpu 2 \
    --lead-ms 5000 \
    --output "$RUN_DIR/channel_trials.csv"

# 4. Receiver-only false-positive controls.
echo "=== Receiver-only controls ==="

python3 experiments/run_channel_experiments.py \
    --no-sender \
    --message 10101010 \
    --durations 100 \
    --levels none,high \
    --trials "$TRIAL_COUNT" \
    --affinity same \
    --cpu 0 \
    --lead-ms 5000 \
    --output "$RUN_DIR/channel_trials.csv"

# 5. Summaries and graphs.
echo "=== Analyzing interference study ==="

python3 experiments/analyze_results.py \
    --input "$RUN_DIR/experiment_runs.csv" \
    --raw "$RUN_DIR/raw_samples.csv" \
    --summary "$RUN_DIR/benchmark_slowdown_summary.csv" \
    --plots-dir "$RUN_DIR/plots" \
    --channel-csv "$RUN_DIR/channel_trials.csv" \
    --channel-metrics "$RUN_DIR/channel_metrics.csv" \
    --channel-summary "$RUN_DIR/channel_summary.csv"

echo "=================================="
echo "Interference study completed!"
echo "Results saved in:"
echo "$RUN_DIR"
echo "=================================="
