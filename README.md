# CPU Scheduling Covert Channel

**Operating Systems — Final Group Project**

## 1. Project Overview

This project investigates covert communication between two Linux processes through CPU scheduling contention, without conventional inter-process communication such as pipes, sockets, or shared memory.

The sender transmits binary information by alternating between CPU-intensive execution and sleeping. The receiver observes variations in CPU execution availability to infer the transmitted bits.

The project evaluates the reliability and performance implications of this communication mechanism under different CPU placements, CPU bandwidth restrictions, transmission durations, and interference levels.

## 2. Research Question

How reliably can two Linux processes transmit information through CPU scheduling contention without conventional inter-process communication, and how do CPU affinity, cgroup CPU bandwidth limits, and scheduling interference affect channel reliability, bit error rate, throughput, and legitimate workload performance?

## 3. Communication Protocol

### Bit Encoding

- **Bit 1:** The sender performs CPU-intensive busy waiting.
- **Bit 0:** The sender sleeps until the scheduled deadline.

### Synchronization

The sender and receiver share a future start timestamp obtained using `CLOCK_MONOTONIC`.

Both processes divide the transmission into fixed-duration time slots. Absolute deadlines limit the accumulation of timing drift between successive slots.

### Preamble and Decoding

Each transmission begins with the eight-bit preamble:

`11110000`

The receiver uses this known pattern to calibrate its decoding threshold before processing the message payload.

### Supported Parameters

- Bit durations: **50 ms, 100 ms, 200 ms**
- Binary message length: **1–1024 bits**
- Standard experimental payload: `10101010`
- Standard preamble: `11110000`

## 4. Technologies and Environment

| Component                  | Technology                                |
| -------------------------- | ----------------------------------------- |
| Core implementation        | C                                         |
| Compiler                   | GCC                                       |
| Automation                 | Bash and Python 3                         |
| Analysis and visualization | Python, Matplotlib                        |
| Operating environment      | Ubuntu 24.04 on WSL2                      |
| CPU affinity               | `taskset`                               |
| CPU quotas                 | cgroup v2, `systemd-run`                |
| CPU interference           | Custom C load generator and `stress-ng` |
| Synchronization            | `CLOCK_MONOTONIC`                       |
| Version control            | Git and GitHub                            |

The final experimental datasets were collected on the integrated WSL2 environment. CPU topology records are included with the final study outputs.

## 5. Repository Structure

```text
CPU-Covert-Channel/
├── src/
│   ├── sender.c
│   ├── receiver.c
│   ├── interference.c
│   ├── benchmark.c
│   ├── protocol.h
│   ├── protocol_test.c
│   ├── receiver_test.c
│   └── timing_test.c
│
├── scripts/
│   ├── build.sh
│   ├── capture_topology.sh
│   ├── baseline.sh
│   ├── sender_timing.sh
│   ├── contended_timing.sh
│   ├── affinity.sh
│   ├── quota.sh
│   ├── channel_trials.py
│   ├── interference.sh
│   ├── run_sender_study.sh
│   ├── run_cpu_controls_study.sh
│   └── run_interference_study.sh
│
├── experiments/
│   ├── run_experiments.py
│   ├── run_channel_experiments.py
│   ├── analyze_results.py
│   ├── analyze_baseline_results.py
│   ├── analyze_sender_timing.py
│   ├── compare_sender_timing.py
│   ├── analyze_throughput.py
│   └── analyze_cpu_controls.py
│
├── results/
│   └── studies/
│       ├── sender/
│       ├── cpu_controls/
│       └── interference/
│
├── docs/
│   ├── baseline_experiments.md
│   ├── receiver_experiments.md
│   └── KARIM_RESULTS.md
│
└── README.md
```

Compiled binaries are generated under `bin/` and excluded from Git.

## 6. Building and Testing

### Prerequisites

The project requires a Linux environment with GCC, Python 3, Bash, `taskset`, `stress-ng`, and a working user-level systemd environment for CPU quota experiments.

Matplotlib is required for generating graphs.

CPU affinity experiments require at least three available logical CPUs (including CPUs 0 and 2). Verify the CPUs available to the process using `<span>taskset -pc $$</span>` before running the studies.

### Build

From the project root:

```bash
bash scripts/build.sh
```

This compiles the sender, receiver, legitimate workload benchmark, and interference generator into `bin/`.

### Receiver Self-Test

```bash
./bin/receiver --self-test
```

### C Tests

```bash
for test in protocol_test receiver_test timing_test; do
    gcc -Wall -Wextra -O2 "src/${test}.c" -o "/tmp/${test}"
    "/tmp/${test}"
done
```

The integrated project was rebuilt and these tests were executed successfully after completing the final experiments.

## 7. Running the Covert Channel

The sender and receiver must use the same:

1. Future `CLOCK_MONOTONIC` start timestamp.
2. Bit duration.
3. Expected payload length.

### Sender Interface

```bash
./bin/sender <bits> <duration_ms> <start_ns> [--timing]
```

### Receiver Interface

```bash
./bin/receiver <message_length> <duration_ms> <start_ns>
```

The `start_ns` value represents a shared future monotonic timestamp in nanoseconds.

### Baseline Example

```bash
bash scripts/baseline.sh 100 10101010 15
```

This executes 15 baseline communication trials using 100 ms bit slots.

## 8. Experimental Methodology

The final evaluation consisted of **825 experimental trials**, with 15 repetitions per condition.

| Study             | Experimental scope                                                 |  Total trials |
| ----------------- | ------------------------------------------------------------------ | ------------: |
| Sender and timing | Baseline, sender-only timing, contention across three durations    |           135 |
| CPU controls      | Affinity, quota performance, communication reliability             |           240 |
| CPU interference  | Workload benchmarks, channel transmissions, receiver-only controls |           450 |
| **Total**   |                                                                    | **825** |

The studies were executed sequentially to reduce interference between different experiment groups.

### Study 1 — Sender and Timing

```bash
bash scripts/run_sender_study.sh 15
```

This study evaluates:

- Baseline communication at 50, 100, and 200 ms.
- Sender timing accuracy without receiver contention.
- Sender timing accuracy with receiver contention.
- Transmission-window throughput derived from timing logs.

### Study 2 — CPU Affinity and Quotas

```bash
bash scripts/run_cpu_controls_study.sh 15
```

This study evaluates:

- Benchmark performance under different CPU placements.
- Benchmark performance at unrestricted, 75%, 50%, 25%, and 10% CPU bandwidth.
- Covert-channel reliability under CPU placement and quota restrictions.

### Study 3 — CPU Interference

```bash
bash scripts/run_interference_study.sh 15
```

This study evaluates:

- Legitimate workload performance under none, low, medium, and high interference.
- Channel reliability across two CPU placements and three bit durations.
- Receiver-only false-positive behavior without a transmitting sender.

The interference experiments use a balanced configuration of 15 repetitions per condition.

Each study runner creates an isolated timestamped output directory containing the measurements and analysis outputs.

For a smaller functionality check, the runners accept `1` instead of `15` as the repetition count.

## 9. Final Experimental Results

### 9.1 Sender Timing Accuracy

Average sender slot-end timing error:

| Bit duration | Sender alone | Sender with receiver |
| ------------ | -----------: | -------------------: |
| 50 ms        |     0.276 ms |             0.575 ms |
| 100 ms       |     0.279 ms |             0.815 ms |
| 200 ms       |     0.259 ms |             0.425 ms |

CPU contention increased average sender timing error at all tested durations.

### 9.2 Transmission-Window Rate

The sender timing study measured the following rates with the receiver present:

| Bit duration | Theoretical rate | Measured rate |
| ------------ | ---------------: | ------------: |
| 50 ms        |    10.000 bits/s |  9.999 bits/s |
| 100 ms       |     5.000 bits/s |  5.000 bits/s |
| 200 ms       |     2.500 bits/s |  2.500 bits/s |

These rates account for the entire transmission window, including the preamble, and exclude the initial synchronization waiting period.

They should not be interpreted as successfully delivered payload goodput.

### 9.3 CPU Affinity Performance

| Configuration               | Mean execution time | Slowdown |
| --------------------------- | ------------------: | -------: |
| Baseline                    |            1.600 ms |   1.00× |
| Same CPU                    |            3.618 ms |   2.26× |
| Sibling CPU configuration   |            1.945 ms |   1.22× |
| Separate-core configuration |            1.905 ms |   1.19× |

Direct same-CPU contention produced the largest measured performance penalty in this study.

### 9.4 CPU Quota Performance

| CPU quota    | Mean execution time | Slowdown |
| ------------ | ------------------: | -------: |
| Unrestricted |            1.688 ms |   1.00× |
| 75%          |            1.769 ms |   1.05× |
| 50%          |            2.423 ms |   1.44× |
| 25%          |           11.548 ms |   6.84× |
| 10%          |           41.571 ms |  24.63× |

Restrictive CPU quotas substantially increased legitimate execution time.

### 9.5 Channel Reliability Under CPU Controls

All conditions used 15 trials at 200 ms per bit.

| Configuration             | Correct messages | Success rate |
| ------------------------- | ---------------: | -----------: |
| Same CPU                  |            15/15 |         100% |
| Sibling CPU configuration |             0/15 |           0% |
| Separate cores            |             0/15 |           0% |
| 75% quota                 |            15/15 |         100% |
| 50% quota                 |            15/15 |         100% |
| 25% quota                 |            15/15 |         100% |
| 10% quota                 |            14/15 |        93.3% |

CPU quotas reduced available execution bandwidth but did not consistently prevent covert communication.

### 9.6 Legitimate Workload Under Interference

| Interference | Mean benchmark time | Slowdown |
| ------------ | ------------------: | -------: |
| None         |            1.383 ms |   1.00× |
| Low          |            1.890 ms |   1.37× |
| Medium       |            2.601 ms |   1.88× |
| High         |            5.913 ms |   4.27× |

High interference produced the largest degradation in legitimate workload performance.

### 9.7 Channel Reliability Under Interference

Exact-message success rates with sender and receiver sharing the same logical CPU:

| Interference | 50 ms | 100 ms | 200 ms |
| ------------ | ----: | -----: | -----: |
| None         |  100% |   100% |   100% |
| Low          |  100% |   100% |   100% |
| Medium       |  100% |   100% |   100% |
| High         | 33.3% |  53.3% |  40.0% |

Across the 135 same-CPU trials with none, low, or medium interference, every message was received correctly.

Under high interference, only **19 of 45** messages were received correctly.

Across the 180 separate-CPU transmissions, **no exact message was received successfully**. Three trials produced complete but incorrect decoded messages.

### 9.8 Receiver-Only False-Positive Controls

| Interference | Decoded messages |  Rate |
| ------------ | ---------------: | ----: |
| None         |             0/15 |    0% |
| High         |             1/15 | 6.67% |

A decoded message was observed once under high interference despite the absence of a transmitting sender.

This demonstrates that scheduling noise can occasionally resemble the expected signal.

## 10. Interpreting Reliability and Throughput

The project distinguishes several measurements:

- **Decode success rate:** Fraction of attempts that produce a complete decoded message.
- **Exact-message success rate:** Fraction of attempts that recover the transmitted payload without errors.
- **Bit error rate (BER):** Fraction of incorrect bits among complete decoded messages.
- **Nominal payload rate:** Payload length divided by the nominal total transmission time, including preamble overhead.
- **Successful-message goodput:** Payload rate adjusted for the proportion of exactly correct messages.

Failed decoding attempts are not assigned an artificial BER of zero.

For the standard eight-bit payload and eight-bit preamble, nominal payload rates are 10, 5, and 2.5 bits/s for 50, 100, and 200 ms slots, respectively.

These nominal rates exclude synchronization startup delay and should not be confused with end-to-end delivery throughput.

## 11. Experimental Evidence

Final evidence is preserved under:

```text
results/studies/
├── sender/
│   └── 20261125T162300Z_56305/
├── cpu_controls/
│   └── 20261125T163850Z_61695/
└── interference/
    └── 20261125T165714Z_65555/
```

The final datasets include:

- Raw sender and receiver logs.
- Individual experimental trial measurements.
- Aggregated summary CSV files.
- CPU topology records.
- Generated graphs.

The complete final evidence is committed to version control.

## 12. Team Responsibilities

### Person 1 — Sender and Timing

- Sender implementation.
- Busy/idle bit encoding.
- Protocol synchronization.
- Configurable transmission durations.
- Baseline communication experiments.
- Sender timing and contention measurements.
- Transmission-rate analysis.

### Person 2 — Receiver and CPU Controls

- Receiver implementation and calibration.
- Bit decoding and reliability measurements.
- CPU affinity experiments.
- cgroup v2 CPU quota experiments.
- Legitimate workload performance under CPU restrictions.

### Person 3 — Interference and Benchmarking

- CPU interference generation.
- Legitimate workload benchmarking.
- Automated interference experiments.
- Receiver-only false-positive controls.
- Result aggregation, analysis, and visualization.

### Shared Responsibilities

- Integration and validation.
- Experimental methodology.
- Comparative analysis.
- Research report.
- Presentation and viva preparation.

## 13. Limitations

- The final experiments were conducted in Ubuntu on WSL2; outcomes may differ on native Linux and other hardware.
- CPU affinity restricts processor placement but does not provide exclusive CPU ownership.
- Background processes and operating system scheduling activity cannot be completely eliminated.
- The experiments primarily used a short, alternating eight-bit payload.
- The tested sender and receiver shared a future start time; synchronization distribution was not part of the covert channel.
- The primary channel measurement relies on contention and may not operate reliably across all CPU placements.
- CPU interference workers were not necessarily pinned to individual CPUs.
- Benchmarks collected within channel trials measure workload performance under active interference but are not simultaneous measurements of the payload transmission itself.
- Some measured throughput values exclude initial waiting and synchronization overhead.
- The results characterize the tested configurations and should not be generalized to every Linux scheduler or CPU topology.

## 14. Conclusion

The experiments demonstrate that CPU scheduling contention can support covert communication between otherwise separate processes.

Communication was highly reliable when both processes shared a logical CPU under low or moderate scheduling interference. Moving the processes to separate CPUs largely prevented reliable decoding in the tested environment.

CPU quotas introduced substantial legitimate workload overhead but did not consistently eliminate the communication channel. High scheduling interference reduced channel reliability while also degrading legitimate benchmark performance and occasionally producing false-positive decoding.

These findings illustrate the relationship between covert-channel reliability, CPU scheduling behavior, and the performance costs of resource restrictions.
