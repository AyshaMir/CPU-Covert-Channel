#!/usr/bin/env bash
# Build Karim tools + optionally compile teammate sender/receiver into bin/
# without modifying their source trees.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CC="${CC:-gcc}"
CFLAGS="${CFLAGS:--O2 -Wall -Wextra -std=c11}"
PARENT="$(cd "$ROOT/.." && pwd)"

# Prefer sender-experiments (has --timing); fall back to feature-sender / main.
SENDER_SRC="${SENDER_SRC:-}"
RECEIVER_SRC="${RECEIVER_SRC:-}"

find_src() {
    local name="$1"
    shift
    local cand
    for cand in "$@"; do
        if [[ -f "$cand" ]]; then
            echo "$cand"
            return 0
        fi
    done
    return 1
}

if [[ -z "$SENDER_SRC" ]]; then
    SENDER_SRC="$(find_src sender \
        "$PARENT/branches/feature-sender-experiments/src/sender.c" \
        "$PARENT/branches/feature-sender/src/sender.c" \
        "$PARENT/repo/src/sender.c" \
        || true)"
fi
if [[ -z "$RECEIVER_SRC" ]]; then
    RECEIVER_SRC="$(find_src receiver \
        "$PARENT/branches/feature-receiver/src/receiver.c" \
        "$PARENT/repo/src/receiver.c" \
        || true)"
fi

cd "$ROOT"
mkdir -p bin

"$CC" $CFLAGS -o bin/benchmark src/benchmark.c -lm
"$CC" $CFLAGS -o bin/interference src/interference.c
echo "Built: bin/benchmark bin/interference"

if [[ -n "${SENDER_SRC:-}" && -f "$SENDER_SRC" ]]; then
    SENDER_DIR="$(dirname "$SENDER_SRC")"
    "$CC" $CFLAGS -I"$SENDER_DIR" -o bin/sender "$SENDER_SRC"
    echo "Built: bin/sender  (from $SENDER_SRC)"
else
    echo "WARN: teammate sender.c not found; channel experiments need SENDER_SRC=..." >&2
fi

if [[ -n "${RECEIVER_SRC:-}" && -f "$RECEIVER_SRC" ]]; then
    RECEIVER_DIR="$(dirname "$RECEIVER_SRC")"
    "$CC" $CFLAGS -I"$RECEIVER_DIR" -o bin/receiver "$RECEIVER_SRC"
    echo "Built: bin/receiver  (from $RECEIVER_SRC)"
else
    echo "WARN: teammate receiver.c not found; channel experiments need RECEIVER_SRC=..." >&2
fi