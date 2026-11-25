
#!/usr/bin/env bash
# Viva demo: build, topology, workload tests, channel tests, and analysis.
# Every quick-demo run uses a separate output directory.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Full research matrix uses its own integration output directory.
if [[ "${1:-}" == "full" ]]; then
    exec bash scripts/run_research_matrix.sh
fi

# Unique directory to preserve results from earlier runs.
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)_$$"
RUN_DIR="$ROOT/results/demo_runs/$RUN_ID"

mkdir -p "$RUN_DIR/plots"

echo "=================================="
echo "CPU Covert Channel - Viva Demo"
echo "=================================="
echo "Results: $RUN_DIR"

# Build all four programs.
bash scripts/build.sh

# Capture CPU topology.
bash scripts/capture_topology.sh

echo "=== Legitimate workload under interference ==="

python3 experiments/run_experiments.py \
    --samples 20 \
    --trials 3 \
    --output "$RUN_DIR/experiment_runs.csv" \
    --raw-output "$RUN_DIR/raw_samples.csv"

echo "=== Covert channel experiments ==="

python3 experiments/run_channel_experiments.py \
    --message 10101010 \
    --durations 100,200 \
    --levels none,low,high \
    --trials 3 \
    --affinity same \
    --cpu 0 \
    --lead-ms 5000 \
    --output "$RUN_DIR/channel_trials.csv"

echo "=== Workload analysis ==="

python3 experiments/analyze_results.py \
    --input "$RUN_DIR/experiment_runs.csv" \
    --raw "$RUN_DIR/raw_samples.csv" \
    --summary "$RUN_DIR/benchmark_slowdown_summary.csv" \
    --plots-dir "$RUN_DIR/plots"

echo "=== Channel analysis ==="

python3 experiments/analyze_results.py \
    --skip-workload \
    --channel-csv "$RUN_DIR/channel_trials.csv" \
    --channel-metrics "$RUN_DIR/channel_metrics.csv" \
    --channel-summary "$RUN_DIR/channel_summary.csv" \
    --plots-dir "$RUN_DIR/plots"

echo "=================================="
echo "Demo completed successfully!"
echo "Results saved to:"
echo "$RUN_DIR"
echo "=================================="
