# CPU Interference, Channel Reliability, and Legitimate Workload Results

**Project:** CPU Scheduling Covert Channel — Operating Systems Final Group Project
**Team member:** Karim
**Evidence:** Final balanced interference study conducted November 25, 2026
**Integrated branch:** `integration/final-experiments`

## 1. Responsibility and objective

Karim implemented the CPU interference generator, legitimate workload benchmark, channel experiment automation, result aggregation, and graphs. The goal was to quantify how additional CPU activity affects both legitimate execution and a scheduling-based covert channel, and to test whether the receiver sometimes detects a payload when no sender exists.

### Main components

- `src/interference.c` — synthetic CPU load generator.
- `src/benchmark.c` — legitimate computation benchmark.
- `scripts/interference.sh` — starts and stops load at none/low/medium/high levels.
- `experiments/run_experiments.py` — repeated legitimate workload benchmarks.
- `experiments/run_channel_experiments.py` — controlled sender/receiver attempts with logs and per-trial CSV records.
- `experiments/analyze_results.py` — summaries, rates, BER, workload comparisons, and plots.
- `scripts/run_interference_study.sh` — integrated final study runner.

The four C programs build together with `scripts/build.sh`.

## 2. Environment and experimental design

The **final** research results below were collected on the integrated Ubuntu/WSL2 study environment. Earlier exploratory work on a separate team machine is not mixed into these final measurements.

- Sender payload: `10101010`; preamble: `11110000`.
- Bit durations: 50, 100, and 200 ms.
- Interference levels: none, low, medium, high.
- Placement: sender and receiver both on logical CPU 0, or sender on CPU 0 and receiver on CPU 2.
- Fifteen repetitions per condition.
- Shared future `CLOCK_MONOTONIC` start time.
- Interference worker counts as recorded in the run's CSVs; workers were not necessarily pinned to the sender's CPU.

| Experiment                    |                     Conditions | Repetitions |        Trials |
| ----------------------------- | -----------------------------: | ----------: | ------------: |
| Legitimate workload benchmark |       Four interference levels |          15 |            60 |
| Same-CPU covert channel       |        3 durations × 4 levels |          15 |           180 |
| Separate-CPU covert channel   |        3 durations × 4 levels |          15 |           180 |
| Receiver-only control         | None/high interference, 100 ms |          15 |            30 |
| **Total**               |        **30 conditions** |             | **450** |

The 360 sender-present channel attempts plus 30 receiver-only controls make 390 channel/control trials. The 60 workload benchmarks are a separate experiment.

## 3. Effect on legitimate workload performance

The dedicated workload benchmark used 20 samples per trial, with 15 trials at each interference level.

| Interference level | Mean trial-average time | SEM across trials | Slowdown vs none |
| ------------------ | ----------------------: | ----------------: | ---------------: |
| None               |             1.383170 ms |       0.013758 ms |          1.000× |
| Low                |             1.889723 ms |       0.119024 ms |          1.366× |
| Medium             |             2.601473 ms |       0.071586 ms |          1.881× |
| High               |             5.912803 ms |       0.294446 ms |          4.275× |

High interference increased mean benchmark time to roughly 4.27 times its no-interference baseline. Within-trial timing variance was also higher under high interference; the mean coefficient of variation was approximately 0.411, compared with 0.047 under none.

## 4. Covert-channel reliability on the same CPU

The following entries are **exact-message successes** out of 15 attempts. These are not merely complete decodes: the received eight-bit payload had to match the sender's payload exactly.

| Interference |        50 ms |       100 ms |       200 ms |
| ------------ | -----------: | -----------: | -----------: |
| None         | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) |
| Low          | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) |
| Medium       | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) |
| High         | 5/15 (33.3%) | 8/15 (53.3%) | 6/15 (40.0%) |

All **135/135** same-CPU messages under none, low, or medium interference were correct. Under high interference, **19/45** were correct.

### High-interference decoding details

| Slot duration | Complete decodes | Exact-message successes | Mean BER on complete decodes |
| ------------- | ---------------: | ----------------------: | ---------------------------: |
| 50 ms         |            10/15 |                    5/15 |                     0.187500 |
| 100 ms        |            13/15 |                    8/15 |                     0.096154 |
| 200 ms        |             7/15 |                    6/15 |                     0.017857 |

The lowest observed mean BER among complete decodes is not necessarily the highest message success rate, because failed or incomplete decodes are excluded from BER but count as unsuccessful messages.

## 5. Covert-channel reliability on separate CPUs

Across **180 sender-present attempts** with sender on logical CPU 0 and receiver on CPU 2:

- **0/180** messages were received exactly.
- Three attempts produced complete but incorrect messages (one at 200 ms/low interference and two at 50 ms/high interference).
- The other 177 attempts produced no complete decoded payload.

This shows that the receiver generally did not observe a reliable signal across these logical CPU placements in the tested implementation. It does **not** prove that all CPU covert channels fail between separate cores or machines.

## 6. Receiver-only false-positive control

The receiver was run without a sender to test whether unrelated scheduling activity could yield decoded bits.

| Interference | Receiver produced a decoded payload | Observed rate |
| ------------ | ----------------------------------: | ------------: |
| None         |                                0/15 |            0% |
| High         |                                1/15 |         6.67% |

The high-interference case is a **false-positive decode event** because a message was decoded in the absence of a sender. It is not a correctly delivered sender message.

## 7. Metrics and interpretation

- **Decode success rate:** fraction of channel attempts producing a complete decoded payload.
- **Message success rate:** fraction producing the *exact* payload transmitted.
- **BER:** incorrect bits / payload bits, **only for complete comparable decodes**. Missing decodes have undefined BER (`nan`), not BER = 0.
- **Raw nominal bit rate:** 1000 / slot duration in milliseconds; includes preamble slots as raw transmitted symbols.
- **Nominal payload rate:** 8 payload bits divided by 16 total slots × slot duration.
- **Successful-message goodput:** nominal payload rate multiplied by exact-message success fraction. This is a nominal-window, successful-message metric; it excludes startup, initial synchronization wait, and retransmissions.
- **Benchmark slowdown:** mean benchmark execution time under a level divided by no-interference mean.

| Slot duration | Nominal raw rate | Nominal payload rate |
| ------------- | ---------------: | -------------------: |
| 50 ms         |        20 bits/s |            10 bits/s |
| 100 ms        |        10 bits/s |             5 bits/s |
| 200 ms        |         5 bits/s |           2.5 bits/s |

The legacy `throughput_bps` field in the channel CSV is an error-adjusted nominal symbol-rate proxy, not confirmed payload goodput. Use `nominal_payload_bps` and `successful_goodput_bps` in the final summary when discussing delivery rates.

### Benchmark timing within channel trials

The channel runner runs its quick benchmark **after** a communication attempt while the selected interference level remains active. This produces a paired observation of background interference performance, **not** a benchmark running concurrently with the payload transmission. The 60-trial dedicated workload study is the primary source for the slowdown results in Section 3.

## 8. Reproduce the final interference study

From the project root:

```bash
bash scripts/build.sh
bash scripts/run_interference_study.sh 15
```

For a one-repetition pilot, run `bash scripts/run_interference_study.sh 1`. Each invocation creates a separate timestamped output directory. Avoid additional CPU-heavy workloads while collecting timing results.

### Verified final evidence

`results/studies/interference/20261125T165714Z_65555/`

| Artifact                           | Contents                                                  |
| ---------------------------------- | --------------------------------------------------------- |
| `experiment_runs.csv`            | 60 dedicated workload trials                              |
| `raw_samples.csv`                | Individual benchmark timing samples                       |
| `benchmark_slowdown_summary.csv` | Dedicated workload means, variability, slowdown           |
| `channel_trials.csv`             | 360 sender-present attempts + 30 receiver-only controls   |
| `channel_metrics.csv`            | Per-attempt channel metrics for sender-present conditions |
| `channel_summary.csv`            | 24 channel condition summaries, 15 attempts each          |
| `channel_logs/`                  | Raw sender and receiver logs                              |
| `cpu_topology.txt`               | CPU layout captured during this study                     |
| `plots/`                         | 16 final performance and channel figures                  |

The final evidence is committed to Git. Earlier demonstration outputs and the superseded `demo.sh` and `run_research_matrix.sh` scripts were removed during repository cleanup.

## 9. Limitations

- WSL2 virtualization and host background activity may influence observed CPU timing.
- Interference workers were not necessarily assigned to a specific logical CPU; worker count is not a direct measure of sender/receiver contention.
- Same and separate CPU placement is based on logical CPU numbers; confirm topology from the recorded `cpu_topology.txt`.
- Trials used the fixed alternating eight-bit payload, not a representative sample of all possible binary messages.
- Fifteen repetitions per condition quantify observed behavior but do not eliminate sampling uncertainty.
- Workload benchmarks measured during channel trials were not simultaneous with sender-to-receiver transmission.
- Nominal goodput excludes initial synchronization waiting, process startup, and retransmission costs.
- The no-sender control examined only two interference conditions at 100 ms.

## 10. Conclusion

The covert channel was highly reliable when sender and receiver shared a logical CPU under none, low, or medium interference, but high interference reduced exact-message success and increased legitimate workload execution time. Moving the processes to separate logical CPUs yielded no correct transmissions in the tested 180 attempts. The receiver-only high-interference control also demonstrated that scheduling noise can occasionally produce a decoded message without a sender. Together, these findings highlight both the potential and the limitations of scheduling-contention covert communication in the evaluated WSL2 environment.
