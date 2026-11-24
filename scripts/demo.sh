#!/usr/bin/env bash
# One-command viva demo: build → topology → workload matrix → channel under interference → analyze.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

chmod +x scripts/*.sh 2>/dev/null || true
sed -i 's/\r$//' scripts/*.sh experiments/*.py 2>/dev/null || true

./scripts/build.sh
./scripts/capture_topology.sh

echo "=== Legitimate workload under interference ==="
python3 experiments/run_experiments.py --fresh --samples 20 --trials 3

if [[ "${1:-}" == "full" ]]; then
  exec bash scripts/run_research_matrix.sh
fi

echo "=== Covert channel (quick: 100/200 ms, none/low/high, same CPU) ==="
python3 experiments/run_channel_experiments.py --fresh \
    --message 10101010 \
    --durations 100,200 \
    --levels none,low,high \
    --trials 3 \
    --affinity same \
    --cpu 0 \
    --lead-ms 5000

python3 experiments/analyze_results.py
python3 experiments/analyze_results.py --skip-workload --channel-csv results/channel_trials.csv

echo "Done. For full research matrix: ./scripts/run_research_matrix.sh or ./scripts/demo.sh full"