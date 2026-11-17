# CPU Scheduling Covert Channels

Operating Systems final group project.

## Research question
How reliably can two Linux processes transmit information through CPU scheduling contention without conventional inter-process communication, and how do CPU affinity, cgroup CPU bandwidth limits, and scheduling interference affect the channel's bit error rate, throughput, and legitimate workload performance?

## Directory guide
- `src/`: C sender/receiver (teammates) — stubs on this branch; do not replace here
- `src/benchmark.c`, `src/interference.c`: Karim — legitimate workload + CPU load generator
- `scripts/`: `interference.sh` (Karim); affinity/quota remain teammate-owned
- `experiments/`: Karim — automation and analysis
- `results/`: measurements (gitignored)

## Karim on this branch (`feature/interference`)

Build and run on **Ubuntu WSL2**:

```bash
./scripts/build.sh
python3 experiments/run_experiments.py --fresh --samples 20 --trials 3
python3 experiments/analyze_results.py
```

Levels: `none`, `low` (1 worker), `medium` (nproc/2), `high` (nproc).
Benchmark matches the receiver-style 1M-add timing probe. BER/throughput when bit strings exist:

```bash
python3 experiments/analyze_results.py --sent-bits 10101010 --received-bits 10101110 --bit-duration-ms 100
```

## Team
- **Ayesha Mir:** sender, timing slots 50/100/200 ms, preamble
- **Prabha Lakhani:** receiver sampling/decoding, affinity, cgroup quotas
- **Karim:** interference, legitimate benchmark, experiment automation, graphs

## Environment
Ubuntu on WSL2.

## Results write-up
See `docs/KARIM_RESULTS.md` (CSVs, plots, what was measured, backlog / sender–receiver dependencies).