
#!/usr/bin/env bash
set -u

DURATION="${1:-200}"
MESSAGE="${2:-10101010}"
TRIALS="${3:-11}"
CPU=0
BASE_DIR="${BASELINE_OUTPUT_DIR:-results/baseline}"

# Validate duration
if [[ ! "$DURATION" =~ ^(50|100|200)$ ]]; then
    echo "Error: Duration must be 50, 100, or 200 ms."
    exit 1
fi

# Validate message: 1 to 1024 binary digits
if [[ ! "$MESSAGE" =~ ^[01]{1,1024}$ ]]; then
    echo "Error: Message must contain 1 to 1024 binary digits."
    exit 1
fi

# Validate trial count
if [[ ! "$TRIALS" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: Trials must be a positive integer."
    exit 1
fi

# Use existing directory names for short messages.
# Use a shortened hash for long messages to avoid
# filesystem filename-length limits.
if (( ${#MESSAGE} <= 200 )); then
    MESSAGE_ID="$MESSAGE"
else
    MESSAGE_HASH=$(
        printf '%s' "$MESSAGE" |
        sha256sum |
        cut -c1-16
    )
    MESSAGE_ID="${#MESSAGE}bits_${MESSAGE_HASH}"
fi

RESULT_DIR="${BASE_DIR}/${DURATION}ms_${MESSAGE_ID}"
LOG_DIR="$RESULT_DIR/raw_logs"

mkdir -p "$LOG_DIR"

echo "=================================="
echo "Baseline CPU Covert Channel Test"
echo "Message: $MESSAGE"
echo "Message length: ${#MESSAGE} bits"
echo "Duration: $DURATION ms"
echo "Trials: $TRIALS"
echo "Logical CPU: $CPU"
echo "Results: $RESULT_DIR"
echo "=================================="

for ((i=1; i<=TRIALS; i++)); do
    TRIAL=$(printf "%02d" "$i")

    RECEIVER_FILE="$LOG_DIR/trial${TRIAL}_receiver.txt"
    SENDER_FILE="$LOG_DIR/trial${TRIAL}_sender.txt"

    # Protect previous experimental results
    if [[ -e "$RECEIVER_FILE" ||
          -e "$SENDER_FILE" ||
          -e "$RESULT_DIR/trial${TRIAL}_receiver.txt" ||
          -e "$RESULT_DIR/trial${TRIAL}_sender.txt" ]]; then

        echo "Trial $TRIAL: Existing results found. Skipping."
        continue
    fi

    echo "Running trial $TRIAL..."

    START=$(python3 -c \
        'import time; print(time.monotonic_ns() + 5_000_000_000)')

    taskset -c "$CPU" \
        ./bin/receiver "${#MESSAGE}" "$DURATION" "$START" \
        > "$RECEIVER_FILE" 2>&1 &
    RP=$!

    taskset -c "$CPU" \
        ./bin/sender "$MESSAGE" "$DURATION" "$START" \
        > "$SENDER_FILE" 2>&1 &
    SP=$!

    wait "$RP"
    RECEIVER_STATUS=$?

    wait "$SP"
    SENDER_STATUS=$?

    if [[ "$RECEIVER_STATUS" -eq 0 &&
          "$SENDER_STATUS" -eq 0 ]] &&
       grep -Fxq "Received message: $MESSAGE" "$RECEIVER_FILE"; then

        echo "Trial $TRIAL: SUCCESS"
    else
        echo "Trial $TRIAL: FAILED"
    fi
done

echo "=================================="
echo "Baseline testing finished."
