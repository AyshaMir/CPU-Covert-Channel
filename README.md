# CPU Scheduling Covert Channels — Karim (`feature/interference`)

## Research question
How reliably can two Linux processes transmit information through CPU scheduling contention, and how do affinity, cgroup quotas, and **scheduling interference** affect BER, throughput, and legitimate workload performance?

## What this branch owns
- `src/benchmark.c`, `src/interference.c` — legitimate probe + CPU load generator
- `scripts/interference.sh`, `build.sh`, `demo.sh`, `capture_topology.sh`
- `experiments/run_experiments.py` — workload slowdown under interference
- `experiments/run_channel_experiments.py` — **sender + receiver** under interference (BER / throughput)
- `experiments/analyze_results.py` — slowdown + channel plots

Teammate `sender.c` / `receiver.c` stay **empty stubs** here. `./scripts/build.sh` compiles them from sibling worktrees into `bin/sender` and `bin/receiver` only.

## Quick start (WSL2)

```bash
./scripts/build.sh
./scripts/capture_topology.sh

# Legitimate workload matrix
python3 experiments/run_experiments.py --fresh --samples 20 --trials 3

# Covert channel under interference (needs bin/sender + bin/receiver)
python3 experiments/run_channel_experiments.py --fresh \
  --message 10101010 --durations 100,200 --levels none,low,high --trials 3 --cpu 0

# No-sender control (false decode baseline)
python3 experiments/run_channel_experiments.py --no-sender \
  --message 10101010 --durations 100 --levels none,high --trials 2 --cpu 0

python3 experiments/analyze_results.py
python3 experiments/analyze_results.py --skip-workload --channel-csv results/channel_trials.csv
```

Or one shot: `./scripts/demo.sh`

## Team
- **Ayesha Mir:** sender, 50/100/200 ms slots, preamble
- **Prabha Lakhani:** receiver decode, affinity, cgroup quotas
- **Karim:** interference, legitimate benchmark, experiment automation, graphs, channel×interference orchestration

## Results
See `docs/KARIM_RESULTS.md`.