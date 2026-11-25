
#!/usr/bin/env bash
# Complete sender study: baseline, timing, contention, and throughput.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TRIALS="${1:-15}"

if ! [[ "$TRIALS" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: Trial count must be a positive integer."
    exit 1
fi

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)_$$"
RUN_DIR="$ROOT/results/studies/sender/$RUN_ID"

BASELINE_DIR="$RUN_DIR/baseline"
TIMING_DIR="$RUN_DIR/timing"

mkdir -p "$BASELINE_DIR" "$TIMING_DIR"

echo "=================================="
echo "Sender Study"
echo "=================================="
echo "Repetitions per condition: $TRIALS"
echo "Results: $RUN_DIR"

# Compile all required programs.
bash scripts/build.sh

# 1. Baseline communication at all supported durations.
echo "=== Baseline communication ==="

for duration in 50 100 200; do
    BASELINE_OUTPUT_DIR="$BASELINE_DIR" \
        bash scripts/baseline.sh "$duration" 10101010 "$TRIALS"
done

# 2. Sender timing without receiver contention.
echo "=== Sender-only timing ==="

TRIALS="$TRIALS" \
TIMING_OUTPUT_DIR="$TIMING_DIR" \
    bash scripts/sender_timing.sh

# 3. Sender timing while competing with receiver.
echo "=== Contended sender timing ==="

TRIALS="$TRIALS" \
TIMING_OUTPUT_DIR="$TIMING_DIR" \
    bash scripts/contended_timing.sh

# 4. Analyze baseline communication.
echo "=== Baseline analysis ==="

python3 experiments/analyze_baseline_results.py \
    --base "$BASELINE_DIR"

# 5. Analyze sender timing.
echo "=== Sender timing analysis ==="

python3 experiments/analyze_sender_timing.py \
    --base "$TIMING_DIR"

# 6. Compare sender-only vs contended timing.
echo "=== Timing comparison ==="

python3 experiments/compare_sender_timing.py \
    --base "$TIMING_DIR" \
    --trials "$TRIALS"

# 7. Analyze transmission throughput.
echo "=== Throughput analysis ==="

python3 experiments/analyze_throughput.py \
    --base "$TIMING_DIR" \
    --trials "$TRIALS"

echo "=================================="
echo "Sender study completed!"
echo "Results saved in:"
echo "$RUN_DIR"
echo "=================================="
