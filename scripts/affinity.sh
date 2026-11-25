
#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BENCHMARK="./bin/benchmark"
SAMPLES="${SAMPLES:-100}"
TRIALS="${TRIALS:-15}"

OUTPUT="${AFFINITY_OUTPUT:-results/integration_affinity_performance.csv}"
TOPOLOGY_OUTPUT="${TOPOLOGY_OUTPUT:-results/integration_cpu_topology.txt}"

mkdir -p "$(dirname "$OUTPUT")"
mkdir -p "$(dirname "$TOPOLOGY_OUTPUT")"

if [[ ! -x "$BENCHMARK" ]]; then
    echo "Benchmark executable not found."
    exit 1
fi

echo "configuration,trial,average_ms" > "$OUTPUT"

run_test() {

    local config="$1"
    local benchmark_cpu="$2"

    for ((trial=1; trial<=TRIALS; trial++)); do

        average=$(taskset -c "$benchmark_cpu" \
            "$BENCHMARK" "$SAMPLES")

        echo "$config,$trial,$average" >> "$OUTPUT"

        echo "$config - Trial $trial: $average ms"

    done
}

# Ensure temporary interference is stopped, even if a test fails.
LOAD_PID=""

cleanup() {
    if [[ -n "$LOAD_PID" ]]; then
        kill "$LOAD_PID" 2>/dev/null || true
        wait "$LOAD_PID" 2>/dev/null || true
        LOAD_PID=""
    fi
}

trap cleanup EXIT INT TERM

echo "Running CPU 0 baseline..."
run_test "baseline" 0

echo "Recording available CPU topology..."
lscpu -e=CPU,CORE,SOCKET,ONLINE > "$TOPOLOGY_OUTPUT"

run_loaded_test() {
    local config="$1"
    local load_cpu="$2"

    echo "Running $config performance test..."

    taskset -c "$load_cpu" stress-ng --cpu 1 &
    LOAD_PID=$!

    sleep 1

    run_test "$config" 0

    cleanup
}

run_loaded_test "same_cpu" 0
run_loaded_test "sibling_cpu" 1
run_loaded_test "separate_cores" 2

echo "Results saved to $OUTPUT"