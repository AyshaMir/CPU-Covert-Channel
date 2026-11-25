
#!/usr/bin/env bash
set -euo pipefail

MESSAGE="10101010"
CPU=0
TRIALS="${TRIALS:-15}"
DURATIONS=(200 100 50)
TIMING_OUTPUT_DIR="${TIMING_OUTPUT_DIR:-results/timing}"

# Run from the repository root
cd "$(dirname "$0")/.."

# Check that the sender executable exists
if [[ ! -x ./bin/sender ]]; then
    echo "Error: Compile sender.c first."
    exit 1
fi

# Check CPU affinity is supported
if ! taskset -pc $$ | grep -Eq '(^|[ :,-])0([,-]|$)'; then
    echo "Error: Check whether logical CPU 0 is available."
    exit 1
fi

echo "===================================="
echo "Sender Timing Accuracy Experiments"
echo "Message: $MESSAGE"
echo "Trials per duration: $TRIALS"
echo "Logical CPU: $CPU"
echo "===================================="

for duration in "${DURATIONS[@]}"; do

    RESULT_DIR="${TIMING_OUTPUT_DIR}/${duration}ms"
    mkdir -p "$RESULT_DIR"

    echo ""
    echo "Testing ${duration} ms bit duration"

    for ((i=1; i<=TRIALS; i++)); do

        TRIAL=$(printf "%02d" "$i")
        OUTPUT="$RESULT_DIR/trial${TRIAL}_sender.txt"

        # Never overwrite previous timing data
        if [[ -e "$OUTPUT" ]]; then
            echo "Trial $TRIAL: Existing result. Skipping."
            continue
        fi

        echo "Running trial $TRIAL..."

        # Schedule sender to start 3 seconds in the future
        START=$(python3 -c \
            'import time; print(time.monotonic_ns() + 3_000_000_000)')

        # Run sender alone with timing instrumentation
        if taskset -c "$CPU" \
            ./bin/sender "$MESSAGE" "$duration" "$START" --timing \
            > "$OUTPUT" 2>&1; then

            if grep -q "TIMING_RESULTS_END" "$OUTPUT"; then
                echo "Trial $TRIAL: COMPLETE"
            else
                echo "Trial $TRIAL: Incomplete timing output"
            fi
        else
            echo "Trial $TRIAL: FAILED"
        fi

    done
done

echo ""
echo "===================================="
echo "Sender timing experiments finished."
echo "Results saved in results/timing/"
echo "===================================="
