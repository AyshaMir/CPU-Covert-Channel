
# Karim — Results, Artifacts, and Remaining Scope

**Project:** CPU Covert Channel via Scheduling Contention
**Member:** Karim
**Development branch:** `feature/interference`
**Integrated branch:** `integration/final-experiments`
**Experimental environment:** WSL2 on `DESKTOP-2AJS0GP`, 4 logical CPUs

---

## 1. Team Responsibilities

| Member           | Responsibility                                                                                                                                     |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ayesha** | Sender implementation, busy/idle bit encoding, preamble, timing synchronization, configurable 50/100/200 ms slots, baseline and timing experiments |
| **Prabha** | Receiver implementation and decoding, CPU affinity experiments, cgroup CPU quota experiments                                                       |
| **Karim**  | Scheduling interference generator, legitimate workload benchmark, automated experiment runners, BER and throughput analysis, performance graphs    |

All three contributions have been combined on the local integration branch.

---

## 2. Implemented Components

### Core Programs

- `src/sender.c` — CPU busy/idle signal transmission (Ayesha).
- `src/receiver.c` — CPU contention measurement and message decoding (Prabha).
- `src/interference.c` — CPU load generation for interference experiments (Karim).
- `src/benchmark.c` — Legitimate workload performance measurement (Karim).

### Build and Execution

- `scripts/build.sh` — Compiles all four C programs from the integrated `src/` directory into `bin/`.
- `scripts/interference.sh` — Starts, stops, and checks interference workers at none, low, medium, and high levels.
- `experiments/run_experiments.py` — Executes legitimate workload experiments under different interference levels.
- `experiments/run_channel_experiments.py` — Executes sender–receiver communication trials under interference and CPU affinity configurations.
- `scripts/run_research_matrix.sh` — Coordinates the workload and channel research matrix.
- `scripts/demo.sh` — Provides demonstration functionality; its commands should be reviewed before running.
- `experiments/analyze_results.py` — Produces workload and channel summaries and visualizations.

### Integrated CPU Controls

- `scripts/affinity.sh` — Measures legitimate workload performance under different CPU affinity configurations.
- `scripts/quota.sh` — Measures legitimate workload performance under different CPU bandwidth quotas.

The sender, receiver, interference generator, and benchmark have been compiled and tested together successfully.

---

## 3. Research Questions Addressed

### 3.1 Does additional CPU load affect legitimate workload performance?

Yes. Karim's experiments measured benchmark execution time under four interference levels.

In the recorded research matrix, high interference produced approximately **2.30× slowdown** relative to the no-interference baseline.

### 3.2 Does scheduling interference affect covert-channel reliability?

Yes. On the same logical CPU, communication succeeded under none, low, and medium interference in the recorded trials.

Under high interference, only 2 of 6 communication trials decoded successfully.

### 3.3 How does CPU placement affect communication?

When the sender and receiver shared logical CPU 0, communication was generally successful under conditions without heavy interference.

When the sender was assigned CPU 0 and the receiver CPU 2, none of Karim's 16 recorded trials decoded successfully.

These results suggest that shared CPU scheduling contention is essential to this implementation's communication mechanism under the tested configurations.

### 3.4 How do bit durations affect communication?

Experiments used 50, 100, and 200 ms bit durations.

The recorded same-CPU results show successful decoding at all three durations under none, low, and medium interference.

Further trials are needed to establish whether one duration is statistically more reliable under heavy interference.

### 3.5 What is the performance cost to legitimate workloads?

The experiments record benchmark execution times under different interference levels.

The `benchmark_avg_ms` field in the channel trial data represents a benchmark run after each channel transmission while the configured interference level is still active.

It should not be described as measuring benchmark execution simultaneously with sender–receiver transmission.

### 3.6 How do CPU quotas affect the covert channel?

Prabha's experiments include sender-quota communication trials at 75%, 50%, 25%, and 10% CPU quotas.

Her recorded results indicate successful decoding in all 20 quota trials.

These results should be analyzed alongside the separate legitimate workload quota benchmarks.

Karim's original interference matrix does not independently vary CPU quota.

---

## 4. Recorded Research Matrix

### 4.1 Legitimate Workload Under Interference

| Interference level |        Mean slowdown |
| ------------------ | -------------------: |
| None               |               1.00× |
| Low                | Approximately 1.36× |
| Medium             | Approximately 1.00× |
| High               | Approximately 2.30× |

The low and medium interference measurements are not strictly monotonic.

Possible explanations include WSL2 scheduling variability, interference placement, and background system activity.

These measurements should be interpreted as observations from the recorded experiments rather than precise universal slowdown factors.

### 4.2 Covert Channel — Same Logical CPU

**Configuration:**

- Sender: CPU 0
- Receiver: CPU 0
- Message: `10101010`
- Preamble: `11110000`
- Two trials per configuration

| Bit duration | None        | Low | Medium | High |
| ------------ | ----------- | --- | ------ | ---- |
| 50 ms        | 2/2 decoded | 2/2 | 2/2    | 1/2  |
| 100 ms       | 2/2 decoded | 2/2 | 2/2    | 0/2  |
| 200 ms       | 2/2 decoded | 2/2 | 2/2    | 1/2  |

**Observations:**

- All 18 trials under none, low, and medium interference decoded successfully.
- Only 2 of 6 trials under high interference decoded successfully.
- The recorded successful decodes had zero bit errors.
- Failed decoding is tracked separately from BER.

**Interpretation:**

The channel demonstrated reliable communication under the tested low-interference configurations.

High interference substantially reduced decoding success in this small experimental sample.

The limited number of trials prevents strong statistical conclusions about differences between bit durations.

### 4.3 Covert Channel — Separate Logical CPUs

**Configuration:**

- Sender: CPU 0
- Receiver: CPU 2
- Bit durations: 100 and 200 ms
- Interference levels: none, low, medium, high

**Result:** 0 successful decodes across 16 trials.

**Interpretation:**

In this implementation, the receiver measures scheduling contention using its own CPU-time-to-wall-time ratio.

When the sender and receiver occupy separate logical CPUs, sender activity may no longer produce a sufficiently distinguishable signal.

The recorded result indicates that separating the processes prevented successful decoding under these tested WSL2 conditions.

This should not be generalized to every possible CPU covert channel or hardware configuration.

### 4.4 No-Sender Control

The receiver was tested without a sender under none and high interference.

In both recorded controls, no payload was successfully decoded.

These results provide a preliminary false-positive check.

However, two trials are insufficient to establish a reliable false-positive rate.

### 4.5 Additional Integration Trial

An additional integration trial was executed on `DESKTOP-V8D55GU` with:

- Sender and receiver on CPU 0
- 100 ms bit duration
- Low interference
- Message `10101010`

**Result:**

- Decoded message: `10101010`
- Bit errors: 0
- BER: 0%
- Benchmark average: 3.7682 ms
- Sender exit code: 0
- Receiver exit code: 0

This trial confirmed that the merged sender, receiver, and interference workflow operated successfully on a second WSL2 environment.

It should be distinguished from Karim's original experimental trials.

---

## 5. Measurement Definitions

### Decoding Success Rate

The proportion of trials where the receiver successfully produced the intended message.

Failed decoding attempts must be counted when calculating communication success rates.

### Bit Error Rate (BER)

The number of incorrect received bits divided by the number of transmitted bits for comparable decoded messages.

If the receiver produces no decoded message, BER is recorded as undefined rather than automatically assigning 0% or 50%.

### Raw Bit Rate

The number of transmitted bit slots per second.

The nominal raw bit rates are:

| Bit duration | Raw bit rate |
| ------------ | -----------: |
| 200 ms       |     5 bits/s |
| 100 ms       |    10 bits/s |
| 50 ms        |    20 bits/s |

### Effective Payload Throughput

Useful successfully delivered payload bits per second, accounting for the preamble and transmission duration.

For an eight-bit message with an eight-bit preamble and no errors, the nominal payload rates are:

| Bit duration | Nominal payload throughput |
| ------------ | -------------------------: |
| 200 ms       |                 2.5 bits/s |
| 100 ms       |                   5 bits/s |
| 50 ms        |                  10 bits/s |

These rates exclude the initial synchronization waiting period.

Karim's original `throughput_bps` column should not automatically be interpreted as measured effective payload throughput.

### Legitimate Workload Slowdown

The ratio of workload execution time under a tested condition to its baseline execution time.

A slowdown above 1.0 indicates increased execution time.

---

## 6. Experimental Artifacts

| File or directory                                                         | Purpose                                                                                |
| ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `results/experiment_runs.csv`                                           | Original interference workload trials                                                  |
| `results/raw_samples.csv`                                               | Individual workload timing samples                                                     |
| `results/benchmark_slowdown_summary.csv`                                | Workload slowdown summary                                                              |
| `results/channel_trials.csv`                                            | Channel communication trials                                                           |
| `results/channel_summary.csv`                                           | Channel reliability summaries                                                          |
| `results/channel_metrics.csv`                                           | Channel metrics                                                                        |
| `results/topology.txt`                                                  | `Preserved CPU topology records from Karim's and Prabha's experimental environments` |
| `results/plots/`                                                        | Original workload and channel visualizations                                           |
| `results/affinity_performance.csv/ and results/quota_performance.csv/ ` | Prabha's original CPUaffinity and quota benchmark results                              |
| `results/channel_logs/`                                                 | Original sender and receiver trial logs where available                                |
| `results/integration_matrix/`                                           | Separate output directory for future integrated research-matrix runs                   |

Original experimental datasets should be preserved during repository cleanup and further analysis.

---

## 7. Reproducing Experiments

### Build

From the repository root:

```bash
bash scripts/build.sh
```

This builds:

```text
bin/sender
bin/receiver
bin/benchmark
bin/interference
```

### Run a Single Channel Experiment

Example: same logical CPU, 100 ms slots, low interference, one trial.

```bash
python3 experiments/run_channel_experiments.py \
    --message 10101010 \
    --durations 100 \
    --levels low \
    --trials 1 \
    --affinity same \
    --cpu 0 \
    --output results/integration_matrix/channel_trials.csv
```

### Run CPU Affinity Benchmark

```bash
bash scripts/affinity.sh
```

### Run CPU Quota Benchmark

```bash
bash scripts/quota.sh
```

### Research Matrix

```bash
bash scripts/run_research_matrix.sh
```

The integrated matrix is being updated to save experiment outputs separately from the original datasets.

Before rerunning the complete matrix, its workflow and output handling must pass final integration testing.

---

## 8. Limitations and Methodological Concerns

### Limited Trial Counts

Karim's original channel matrix contains two trials per configuration.

Additional repetitions are needed to estimate reliability more confidently.

### Interference Placement

Interference workers are not necessarily restricted to the same logical CPU as the sender and receiver.

Therefore, the number of workers alone does not guarantee a particular level of direct contention.

Future controlled interference trials should explicitly record or control worker CPU placement.

### Decoding Failures

Receiver failures must remain visible in the analysis.

A trial that produces no decoded message represents unsuccessful communication, even if a numerical BER cannot be calculated.

### Throughput Interpretation

Raw bit rate and effective payload throughput are different quantities.

The report must distinguish them and account for protocol overhead.

### Workload Measurement Timing

The benchmark executed by Karim's channel runner is measured after the channel transmission, while interference remains active.

Consequently, the result measures performance under the configured background interference, not simultaneous channel-and-benchmark contention.

### Environment Differences

Results were collected across different WSL2 environments and CPU topologies.

Direct comparisons between machines must account for these differences.

### Experimental Variability

CPU frequency, host activity, operating-system scheduling, and background workloads may influence timing and performance measurements.

These are especially relevant when interpreting unexpected speedups or non-monotonic results.

---

## 9. Remaining Work

| Item                                         | Status                                       |
| -------------------------------------------- | -------------------------------------------- |
| Sender and receiver integration              | Completed                                    |
| Integrated build system                      | Completed and tested                         |
| Same-CPU communication                       | Completed                                    |
| Separate-CPU communication trials            | Completed; further validation recommended    |
| Interference workload experiments            | Completed                                    |
| Covert-channel interference experiments      | Completed; additional trials recommended     |
| CPU affinity benchmark                       | Completed and tested                         |
| CPU quota benchmark                          | Completed and tested                         |
| Sender-quota channel trials                  | Existing Prabha results; final audit pending |
| Controlled interference CPU placement        | Pending                                      |
| Consistent BER and decoding-success analysis | Pending                                      |
| Standardized effective throughput            | Pending                                      |
| Additional representative trials             | Pending                                      |
| Repository cleanup                           | In progress                                  |
| Final README and reproducibility testing     | Pending                                      |
| Final report and presentation                | Pending                                      |
| Merge integrated work into `main`          | Pending                                      |

---

## 10. Summary for Presentation

Karim implemented scheduling interference, legitimate workload benchmarking, and automated channel experiments.

His recorded findings show that:

- A normal workload experienced approximately 2.30× slowdown under high interference.
- Same-CPU covert communication decoded successfully under none, low, and medium interference in the tested trials.
- High interference reduced decoding success to 2 of 6 trials.
- Sender–receiver separation across CPU 0 and CPU 2 prevented successful decoding in all 16 tested trials.

Together with Ayesha's sender and timing experiments and Prabha's receiver and CPU-control experiments, these results demonstrate a working CPU scheduling covert channel and provide evidence about its reliability, limitations, and performance trade-offs.

The findings are specific to the tested implementation and environments, and additional controlled trials are needed for stronger statistical conclusions.
