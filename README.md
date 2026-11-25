
# CPU Scheduling Covert Channel

Operating Systems Final Group Project

## 1. Project Overview

This project investigates covert communication between two Linux
processes using CPU scheduling contention.

The sender and receiver communicate without using conventional
inter-process communication mechanisms such as pipes, sockets,
or shared memory.

Instead, the sender alternates between CPU-intensive execution
and sleeping. The receiver observes changes in its available
CPU execution time to decode binary information.

The project also investigates how CPU scheduling, processor
affinity, CPU quotas, and interference affect communication
reliability and system performance.

## 2. Research Question

How reliably can two Linux processes transmit information
through CPU scheduling contention without conventional
inter-process communication, and how do CPU affinity,
cgroup CPU bandwidth limits, and scheduling interference
affect the channel's bit error rate, throughput, and
legitimate workload performance?

## 3. Communication Protocol

### Bit Encoding

- Bit 1: Sender performs CPU-intensive busy waiting.
- Bit 0: Sender sleeps until its scheduled deadline.

### Synchronization

The sender and receiver use a shared future start timestamp
based on CLOCK_MONOTONIC.

Each transmitted bit occupies a fixed-duration time slot.

Absolute deadlines are used to prevent individual scheduling
delays from automatically shifting subsequent time slots.

### Preamble

Each transmission begins with:

11110000

The receiver uses this known eight-bit preamble to calculate
a decoding threshold.

### Supported Bit Durations

- 50 ms
- 100 ms
- 200 ms

### Message Length

The implementation accepts binary messages containing
1 to 1024 bits.

## 4. Technologies and Environment

- Language: C
- Analysis and automation: Python 3
- Shell scripting: Bash
- Operating system: Ubuntu on WSL2
- Compiler: GCC
- CPU affinity: taskset
- CPU bandwidth restrictions: cgroup v2 / systemd-run
- Timing clock: CLOCK_MONOTONIC
- Version control: Git and GitHub

Experiments were performed using the available WSL2
environments of the team members.

## 5. Repository Structure

src/
    sender.c
    receiver.c
    protocol.h
    protocol_test.c
    receiver_test.c
    timing_test.c

scripts/
    baseline.sh
    sender_timing.sh
    contended_timing.sh
    affinity.sh
    quota.sh
    interference.sh

experiments/
    analyze_results.py
    analyze_sender_timing.py
    compare_sender_timing.py
    analyze_throughput.py
    run_experiments.py

results/
    baseline/
    timing/
    initial_contention.csv
    cpu_quota_results.csv

docs/
    baseline_experiments.md
    receiver_experiments.md

README.md

Some experiment-control and automation scripts remain
placeholders while team integration continues.

## 6. Building the Programs

Compile the sender:

gcc -Wall -Wextra -O2 src/sender.c -o sender

Compile the receiver:

gcc -Wall -Wextra -O2 src/receiver.c -o receiver

The compiled executables are excluded from version control.

### Receiver Self-Test

./bin/receiver --self-test

This runs the receiver's built-in synthetic decoding test.

## 7. Running a Communication Experiment

The sender and receiver must use the same:

- Future CLOCK_MONOTONIC start timestamp
- Bit duration
- Expected message length

The following script runs a baseline communication experiment:

bash scripts/baseline.sh 100 10101010 11

Arguments:

1. Bit duration in milliseconds
2. Binary message
3. Number of trials

This example executes 11 trials using a 100 ms bit
duration and the message 10101010.

Both processes are pinned to logical CPU 0.

Raw output is saved locally under results/baseline/.

The sender and receiver can also be executed independently
using their command-line interfaces:

./bin/sender <bits></bits> <duration_ms> <start_ns> [--timing]

./bin/receiver <message_length> <duration_ms> <start_ns>

The start_ns argument must represent a shared future
CLOCK_MONOTONIC timestamp in nanoseconds.

## 8. Sender Timing Experiments

### Sender-Only Timing

Run:

bash scripts/sender_timing.sh

This evaluates sender timing accuracy at 50, 100,
and 200 ms without a competing receiver.

### Sender and Receiver Contention

Run:

bash scripts/contended_timing.sh

This runs both processes on logical CPU 0 while
recording sender timing measurements.

Each condition uses:

- Message: 10101010
- Preamble: 11110000
- 10 trials per duration

### Timing Analysis

Run:

python3 experiments/analyze_sender_timing.py

python3 experiments/compare_sender_timing.py

The scripts calculate scheduled deadline errors and
compare sender-only execution with sender–receiver
contention.

## 9. Throughput Analysis

Run:

python3 experiments/analyze_throughput.py

This analyzes existing sender timing logs to calculate:

- Theoretical payload throughput
- Measured transmission duration
- Measured transmission-window throughput
- Initial transmission start delay

The reported transmission-window throughput excludes
the initial synchronization waiting period.

## 10. Experimental Results

### Baseline Communication

39 baseline communication trials were completed.

- Successful transmissions: 39/39
- Incorrect message bits: 0/308
- Observed BER: 0%

### Sender Timing Experiments

30 sender-only timing trials were completed.

30 additional sender–receiver timing trials were completed.

Across these conditions, 960 bit timing records were collected.

All 30 sender–receiver timing trials successfully
decoded the transmitted message.

### Sender Timing Comparison

| Duration | Alone Avg End Error | Contended Avg End Error |
| -------- | ------------------: | ----------------------: |
| 200 ms   |         0.246362 ms |             0.840597 ms |
| 100 ms   |         0.210907 ms |             0.781756 ms |
| 50 ms    |         0.239125 ms |             0.652424 ms |

### Measured Payload Throughput

| Duration |   Theoretical | Sender + Receiver |
| -------- | ------------: | ----------------: |
| 200 ms   |  2.500 bits/s |   2.499923 bits/s |
| 100 ms   |  5.000 bits/s |   4.999657 bits/s |
| 50 ms    | 10.000 bits/s |   9.990655 bits/s |

The measurements show increased sender deadline errors
under CPU contention, while successful communication
and near-theoretical transmission-window throughput
were maintained in the tested conditions.

These results are preliminary and do not establish
error-free communication under all scheduling conditions.

## 11. CPU Affinity and Quota Experiments

Preliminary CPU contention and CPU quota experiments
are documented in:

docs/receiver_experiments.md

The available results investigate:

- Benchmark execution time under CPU contention
- Same-CPU versus separate-CPU configurations
- CPU bandwidth restrictions using cgroup v2

These initial performance experiments do not independently
establish the effects of quotas on covert-channel BER.

Further integration with communication experiments
is part of the remaining group work.

## 12. Experimental Data

Communication summaries:

results/baseline/

Sender timing and throughput summaries:

results/timing/

CPU contention measurements:

results/initial_contention.csv

CPU quota measurements:

results/cpu_quota_results.csv

Important analyzed CSV datasets are included in the
repository.

Raw experiment logs are excluded from version control
and retained locally. Scripts that regenerate summaries
from raw logs require those local files.

## 13. Team Responsibilities

### Person 1 — Sender and Timing Experiments

- Sender implementation
- Busy/idle bit encoding
- CLOCK_MONOTONIC synchronization
- Configurable bit durations
- Baseline communication testing
- Sender timing accuracy
- Contended timing comparison
- Transmission-speed analysis
- Experimental documentation

### Person 2 — Receiver and CPU Controls

- Receiver implementation and decoding
- CPU affinity experiments
- cgroup v2 CPU quota experiments
- Scheduling contention measurements
- Communication reliability under CPU restrictions

### Person 3 — Interference and Benchmarking

- Interference workload generation
- Legitimate workload benchmarking
- Experiment automation
- Performance and reliability measurements
- Result aggregation and graphs

### Shared Responsibilities

- Integration and testing
- Final experimental comparisons
- Research report
- Presentation
- Viva preparation

## 14. Limitations

- Experiments primarily use Ubuntu WSL2.
- CPU affinity does not guarantee exclusive CPU access.
- Background scheduling activity is not fully controlled.
- Most communication tests used short binary messages.
- The baseline experiments introduced no deliberate
  additional interference.
- Sender timing measurements do not capture every
  scheduler interruption.
- Measured transmission-window rates exclude startup
  and synchronization waiting overhead.
- Results may differ on other operating systems,
  processors, or workload configurations.

## 15. Remaining Group Work

- Integrate affinity and quota results with communication tests.
- Integrate scheduling interference experiments.
- Compare bit error rate, throughput, and workload overhead.
- Generate final comparative graphs.
- Complete the research report and presentation.

## 16. Interference and Workload Experiments

Karim implemented the interference generation, legitimate
workload benchmarking, and automated channel experiments.

### Components

- `src/interference.c`: CPU load generator
- `src/benchmark.c`: Legitimate workload benchmark
- `scripts/interference.sh`: Configurable CPU interference
- `experiments/run_experiments.py`: Workload slowdown analysis
- `experiments/run_channel_experiments.py`: Channel experiments
- `scripts/run_research_matrix.sh`: Full experiment matrix
- `scripts/demo.sh`: Demonstration runner

### Experimental Conditions

Interference levels:

- None
- Low
- Medium
- High

CPU configurations:

- Sender and receiver on the same logical CPU
- Sender and receiver on separate logical CPUs

Bit durations:

- 50 ms
- 100 ms
- 200 ms

### Preliminary Findings

The interference experiments showed:

- Successful decoding under none, low, and medium
  interference when sharing CPU 0.
- Reduced decoding success under high interference.
- No successful decoding in the tested separate-CPU
  configurations.
- Approximately 2.30x legitimate workload slowdown
  under high interference.

These results were obtained on Karim's WSL2 environment
and should not be generalized without further testing.

### Experimental Evidence

- `docs/KARIM_RESULTS.md`
- `results/channel_trials.csv`
- `results/channel_summary.csv`
- `results/benchmark_slowdown_summary.csv`
- `results/plots/`

### Integration Note

Karim's original build script expects separate teammate
worktrees. Its build paths must be adapted to the combined
repository before running the full experiment matrix.

The final integration will also standardize throughput
definitions and verify experiment reproducibility.
