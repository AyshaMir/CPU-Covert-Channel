
#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BENCHMARK="./bin/benchmark"

SAMPLES="${SAMPLES:-100}"
TRIALS="${TRIALS:-15}"

OUTPUT="${QUOTA_OUTPUT:-results/integration_quota_performance.csv}"
mkdir -p "$(dirname "$OUTPUT")"

if [[ ! -x "$BENCHMARK" ]]; then
    echo "Benchmark executable not found."
    exit 1
fi

echo "quota,trial,average_ms" > "$OUTPUT"

echo "Running unrestricted benchmark..."

for ((trial=1; trial<=TRIALS; trial++)); do

    average=$(taskset -c 0 "$BENCHMARK" "$SAMPLES")

    echo "unrestricted,$trial,$average" >> "$OUTPUT"

    echo "Unrestricted - Trial $trial: $average ms"

done

for quota in 75 50 25 10; do

    echo "Testing CPU quota: $quota%"

    for ((trial=1; trial<=TRIALS; trial++)); do

        average=$(systemd-run --user --scope --quiet \
            -p "CPUQuota=${quota}%" \
            taskset -c 0 "$BENCHMARK" "$SAMPLES")

        echo "$quota,$trial,$average" >> "$OUTPUT"

        echo "Quota $quota% - Trial $trial: $average ms"

    done

done

echo "Results saved to $OUTPUT"
