# CPU Scheduling Covert Channels

Operating Systems final group project.

## Research question
How reliably can two Linux processes transmit information through CPU scheduling contention without conventional inter-process communication, and how do CPU affinity, cgroup CPU bandwidth limits, and scheduling interference affect the channel's bit error rate, throughput, and legitimate workload performance?

## Project status
Repository skeleton only. Implementation and experiments have not started.

## Directory guide
- `src/`: C sender and receiver (Ayesha)
- `scripts/`: CPU affinity and quota controls (Prabha); interference scripts (Person 3)
- `experiments/`: experiment automation and analysis (Person 3)
- `results/`: generated measurements (not committed)
- `docs/`: research notes and report materials

## Planned experiments
- Bit durations: 50 ms, 100 ms, 200 ms
- Same vs separate logical CPU affinity
- cgroup v2 CPU quotas
- Scheduling interference and legitimate workload impact
- Optional cross-device reproducibility comparison (8 GB vs 16 GB; not a RAM-only causal test)

## Team responsibilities
- **Ayesha Mir:** sender/receiver C programs, timing synchronization and decoding, configurable bit durations, short baseline tests.
- **Prabha Lakhani:** affinity/cgroup controls and isolation experiments.
- **Third member (name pending):** scheduling interference, legitimate workload benchmarking, automation and graphs.
- **Everyone:** integration, analysis, documentation, presentation and viva.

## Environment
Ubuntu on WSL2. Build/run instructions will be added when implementation begins.
