# Sender, Baseline Communication, and Timing Experiments

**Project:** CPU Scheduling Covert Channel — Operating Systems Final Group Project
**Team member:** Ayesha
**Evidence:** Final 15-repetition study conducted November 25, 2026

## 1. Objective

Evaluate communication using CPU scheduling contention, characterize sender timing precision with and without a competing receiver, and compare nominal payload rate with measured transmission-window rate.

The sender represents `1` using CPU-intensive busy waiting and `0` by sleeping until an absolute deadline. The receiver infers the signal from scheduling contention without pipes, sockets, or shared memory.

## 2. Experimental setup

- Operating environment: Ubuntu on WSL2, on the integrated study machine.
- Implementation: C; automation: Bash and Python 3.
- Timing and synchronization: `CLOCK_MONOTONIC` and shared future start timestamps.
- CPU placement: sender and receiver pinned to logical CPU 0 for communication/contended trials.
- Preamble: `11110000` (8 bits); payload: `10101010` (8 bits).
- Slot durations: 50, 100, and 200 ms.
- Repetitions: 15 **per condition**; no deliberately added interference.
- CPU topology and background activity are not fully controlled by CPU affinity.

### Study design

| Experiment                                |           Conditions | Repetitions |        Trials |
| ----------------------------------------- | -------------------: | ----------: | ------------: |
| Baseline sender-to-receiver communication | Three slot durations |          15 |            45 |
| Sender-only timing                        | Three slot durations |          15 |            45 |
| Sender timing with receiver contention    | Three slot durations |          15 |            45 |
| **Total**                           |       **Nine** |             | **135** |

Timing logs contain 16 bit slots per trial (preamble plus payload). The two timing conditions therefore produced 1,440 per-bit records in total; the sender-only analysis contains 720 of those records. Throughput was **calculated from these existing 90 timing trials**, not collected as a separate experiment.

## 3. Protocol and timing measurements

The sender and receiver agree on a future monotonic start time, slot duration, and payload length. Absolute slot boundaries reduce accumulated drift, but individual wakeups or CPU scheduling delays can still shift actual execution times.

The sender's timing instrumentation records scheduled and actual start/end timestamps for each bit. The key metrics are:

- **Start error:** actual bit start minus scheduled bit start.
- **End error:** actual bit end minus scheduled bit end.
- **Relative end error:** mean end error divided by slot duration, expressed as a percentage.

This is a measurement of processing-boundary deviations, not a complete trace of scheduler activity.

## 4. Final sender timing results

Each table row summarizes 15 trials and 240 bit intervals.

| Slot duration | Alone: mean end error | Contended: mean end error | Alone: maximum end error | Contended: maximum end error |
| ------------- | --------------------: | ------------------------: | -----------------------: | ---------------------------: |
| 50 ms         |           0.275791 ms |               0.574772 ms |              3.327076 ms |                  4.052566 ms |
| 100 ms        |           0.278965 ms |               0.814862 ms |              6.516821 ms |                  6.921566 ms |
| 200 ms        |           0.259335 ms |               0.424647 ms |              0.876289 ms |                  5.696431 ms |

**Interpretation:** Mean end errors increased when the receiver competed with the sender on the same CPU at every tested duration. At 50 ms, a similar absolute delay consumes a larger fraction of the bit interval than at 200 ms. Some individual end errors exceeded 1 ms, so a claim that *all* bit intervals stayed below 1 ms would be incorrect for this final dataset.

### Busy versus idle timing

| Slot duration | Alone: busy end error | Alone: idle end error | Contended: busy end error | Contended: idle end error |
| ------------- | --------------------: | --------------------: | ------------------------: | ------------------------: |
| 50 ms         |           0.028560 ms |           0.523021 ms |               0.775693 ms |               0.373852 ms |
| 100 ms        |           0.002579 ms |           0.555351 ms |               1.285969 ms |               0.343755 ms |
| 200 ms        |           0.000588 ms |           0.518082 ms |               0.719008 ms |               0.130285 ms |

Without a receiver, busy waiting had very small mean end errors, while sleep/wakeup introduced higher mean idle end errors. With contention, busy execution was itself delayed by competition for the CPU.

## 5. Transmission-window throughput

An eight-bit payload follows an eight-bit preamble. The nominal payload rate is therefore:

`payload bits / ((preamble bits + payload bits) × bit duration)`

The analysis measures duration from the **scheduled start** of the first slot through the actual end of the last slot; it excludes the initial wait for the scheduled start time.

| Slot duration | Nominal payload rate | Measured sender-only window rate | Measured contended window rate |
| ------------- | -------------------: | -------------------------------: | -----------------------------: |
| 50 ms         |        10.000 bits/s |                  9.993382 bits/s |                9.998929 bits/s |
| 100 ms        |         5.000 bits/s |                  4.998482 bits/s |                4.999690 bits/s |
| 200 ms        |         2.500 bits/s |                  2.499569 bits/s |                2.499929 bits/s |

The rates remain near nominal even though contention increases timing error. **These are sender transmission-window rates, not confirmed delivery goodput.** Sender-only runs have no receiving process. The study does not measure process launch, initial synchronization wait, or retransmission overhead as part of these rates.

## 6. Baseline communication

The final baseline study executed **45 transmissions**, with 15 trials at each of 50, 100, and 200 ms, using the standard eight-bit payload. The combined CSV contains 45 records. Detailed outcomes and decoding values should be read directly from that CSV rather than inferred from timing-rate measurements.

The earlier exploratory message-pattern tests and their old output paths are *not* part of the final 135-trial evidence set. They are not used to derive the final statistics in this document.

## 7. Reproduce the study

From the repository root:

```bash
bash scripts/build.sh
bash scripts/run_sender_study.sh 15
```

For a small functionality pilot, use `bash scripts/run_sender_study.sh 1` instead. Every run produces a new timestamped directory, without overwriting the final study evidence.

### Verified final evidence

`results/studies/sender/20261125T162300Z_56305/`

- `baseline/baseline_combined_summary.csv` — 45 baseline communication records.
- `timing/sender_timing_all.csv` — 720 sender-only per-bit measurements.
- `timing/sender_timing_comparison_all.csv` — 1,440 per-bit measurements across both timing conditions.
- `timing/sender_timing_comparison_summary.csv` — timing comparisons above.
- `timing/throughput_all.csv` — 90 measured timing-trial rate records.
- `timing/throughput_summary.csv` — measured window-rate comparisons above.
- Baseline and timing subfolders contain preserved raw sender/receiver logs.

Analysis source: `experiments/analyze_baseline_results.py`, `analyze_sender_timing.py`, `compare_sender_timing.py`, and `analyze_throughput.py`.

## 8. Limitations

- All final sender measurements come from the tested WSL2 environment and CPU configuration.
- The repeated payload `10101010` does not establish reliability for arbitrary payloads or lengths.
- Trials were not randomized or interleaved between conditions; background system activity can vary over time.
- CPU affinity does not imply exclusive CPU ownership.
- The provided future start timestamp is shared out of band; synchronization itself is not transmitted covertly.
- Results for interference, CPU quotas, and end-to-end delivery success are analyzed separately in the CPU-controls and interference studies.

## 9. Summary

The sender maintained transmission-window rates close to their nominal values across all slot durations, while contention with the receiver increased mean timing errors. These results characterize the sender's timing behavior; the other two studies establish how placement, quota limits, and deliberate interference affect communication success and legitimate workload performance.
