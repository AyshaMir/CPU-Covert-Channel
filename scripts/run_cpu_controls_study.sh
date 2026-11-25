
#!/usr/bin/env bash
# Complete CPU controls study: affinity, quotas, and channel reliability.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TRIAL_COUNT="${1:-15}"

if ! [[ "$TRIAL_COUNT" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: Trial count must be a positive integer."
    exit 1
fi

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)_$$"
RUN_DIR="$ROOT/results/studies/cpu_controls/$RUN_ID"

# Preserve existing results; never reuse an output directory.
mkdir -p "$RUN_DIR"
echo "=================================="
echo "CPU Controls Study"
echo "=================================="
echo "Repetitions per condition: $TRIAL_COUNT"
echo "Results: $RUN_DIR"

# Build all required programs.
bash scripts/build.sh

# Record topology separately for this study.
bash scripts/capture_topology.sh "$RUN_DIR/cpu_topology.txt"

# 1. CPU affinity performance.
echo "=== CPU affinity performance ==="

TRIALS="$TRIAL_COUNT" \
AFFINITY_OUTPUT="$RUN_DIR/affinity_performance.csv" \
TOPOLOGY_OUTPUT="$RUN_DIR/affinity_cpu_topology.txt" \
    bash scripts/affinity.sh

# 2. CPU quota performance.
echo "=== CPU quota performance ==="

TRIALS="$TRIAL_COUNT" \
QUOTA_OUTPUT="$RUN_DIR/quota_performance.csv" \
    bash scripts/quota.sh

# 3. Covert-channel reliability under CPU controls.
echo "=== Channel reliability ==="

python3 scripts/channel_trials.py \
    --trials "$TRIAL_COUNT" \
    --output-dir "$RUN_DIR/channel"

# 4. Generate report-ready summaries and graphs.
echo "=== CPU controls analysis ==="

python3 experiments/analyze_cpu_controls.py \
    --run-dir "$RUN_DIR"

echo "=================================="
echo "CPU controls study completed!"
echo "Results saved in:"
echo "$RUN_DIR"
echo "=================================="
