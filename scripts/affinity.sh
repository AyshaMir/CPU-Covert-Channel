
#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BENCHMARK="./bin/benchmark"
SAMPLES=100
TRIALS=5

OUTPUT="results/affinity_performance.csv"

mkdir -p results

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

echo "Running CPU 0 baseline..."
run_test "baseline" 0

echo "Recording available CPU topology..."
lscpu -e=CPU,CORE,SOCKET,ONLINE \
    > results/cpu_topology.txt

echo "Running same CPU performance test..."
taskset -c 0 stress-ng --cpu 1 --timeout 10s &
LOAD_PID=$!
sleep 1

run_test "same_cpu" 0

wait "$LOAD_PID"

echo "Running sibling CPU performance test..."
taskset -c 1 stress-ng --cpu 1 --timeout 10s &
LOAD_PID=$!
sleep 1

run_test "sibling_cpu" 0

wait "$LOAD_PID"

echo "Running separate core performance test..."
taskset -c 2 stress-ng --cpu 1 --timeout 10s &
LOAD_PID=$!
sleep 1

run_test "separate_cores" 0

wait "$LOAD_PID"

echo "Results saved to $OUTPUT"
