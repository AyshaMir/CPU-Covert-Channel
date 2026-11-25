
#!/usr/bin/env bash
set -euo pipefail

MESSAGE="10101010"
CPU=0
TRIALS=10
DURATIONS=(200 100 50)

cd "$(dirname "$0")/.."

if [[ ! -x ./bin/sender || ! -x ./bin/receiver ]]; then
    echo "Error: Compile sender and receiver first."
    exit 1
fi

echo "===================================="
echo "Contended Sender Timing Experiments"
echo "Message: $MESSAGE"
echo "CPU: $CPU"
echo "Trials per duration: $TRIALS"
echo "===================================="

for duration in "${DURATIONS[@]}"; do
    RESULT_DIR="results/timing/contended/${duration}ms"
    mkdir -p "$RESULT_DIR"

    echo ""
    echo "Testing ${duration} ms"

    for ((i=1; i<=TRIALS; i++)); do
        TRIAL=$(printf "%02d" "$i")

        SENDER_LOG="$RESULT_DIR/trial${TRIAL}_sender.txt"
        RECEIVER_LOG="$RESULT_DIR/trial${TRIAL}_receiver.txt"

        if [[ -e "$SENDER_LOG" || -e "$RECEIVER_LOG" ]]; then
            echo "Trial $TRIAL: Existing results. Skipping."
            continue
        fi

        echo "Running trial $TRIAL..."

        START=$(python3 -c \
            'import time; print(time.monotonic_ns() + 5_000_000_000)')

        taskset -c "$CPU" \
            ./bin/receiver "${#MESSAGE}" "$duration" "$START" \
            > "$RECEIVER_LOG" 2>&1 &
        RP=$!

        taskset -c "$CPU" \
            ./bin/sender "$MESSAGE" "$duration" "$START" --timing \
            > "$SENDER_LOG" 2>&1 &
        SP=$!

        if wait "$RP"; then
            RECEIVER_STATUS=0
        else
            RECEIVER_STATUS=$?
        fi

        if wait "$SP"; then
            SENDER_STATUS=0
        else
            SENDER_STATUS=$?
        fi

        if [[ "$SENDER_STATUS" -eq 0 &&
              "$RECEIVER_STATUS" -eq 0 ]] &&
           grep -q "TIMING_RESULTS_END" "$SENDER_LOG" &&
           grep -Fxq "Received message: $MESSAGE" "$RECEIVER_LOG"; then

            echo "Trial $TRIAL: SUCCESS"

        else
            echo "Trial $TRIAL: FAILED (check saved logs)"
        fi
    done
done

echo ""
echo "===================================="
echo "Contended timing experiments finished."
echo "===================================="
