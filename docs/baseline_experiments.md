
# Baseline CPU Covert Channel Experiments

## 1. Objective

To evaluate CPU covert-channel communication between two Linux processes using CPU scheduling contention.

The experiments investigate:

- Whether the sender and receiver can communicate without conventional IPC.
- How bit duration affects communication reliability and transmission speed.
- Whether different binary messages can be decoded correctly.
- How accurately the sender follows its scheduled bit deadlines.
- How CPU scheduling affects busy and idle intervals.

## 2. Experimental Setup

- Environment: Ubuntu on WSL2
- Implementation language: C
- CPU affinity: Logical CPU 0
- Affinity tool: `taskset`
- Synchronization: `CLOCK_MONOTONIC`
- Preamble: `11110000`
- Bit durations: 50, 100, and 200 ms
- Added interference: None
- Background system activity: Not fully isolated

### Communication Protocol

The sender encodes binary information through CPU activity:

- Bit `1`: CPU busy waiting.
- Bit `0`: Sleeping until an absolute deadline.

The receiver measures its own CPU execution time relative to elapsed wall-clock time.

CPU Time Ratio = Process CPU Time / Elapsed Time

Lower ratios indicate greater CPU contention, while higher ratios indicate less contention.

Both processes use a shared future start timestamp and fixed bit durations.

The receiver uses the known preamble to calculate a decoding threshold before interpreting the message.

## 3. Initial Communication Test

### Trial 01 — 200 ms

- Bit duration: 200 ms
- Preamble: `11110000`
- Transmitted message: `10101010`
- Received message: `10101010`
- Total transmitted bits: 16
- Preamble bits: 8
- Message bits: 8
- Incorrect message bits: 0/8
- Bit error rate (BER): 0%
- Busy reference: 0.500702
- Idle reference: 0.999890
- Decoding threshold: 0.750296
- Result: Successful

### Observations

The receiver successfully decoded all eight message bits.

Busy intervals produced CPU-time ratios near 0.50, while idle intervals produced ratios near 1.00.

The receiver calculated its threshold using the preamble:

Threshold = (Busy Reference + Idle Reference) / 2

Threshold = (0.500702 + 0.999890) / 2

Threshold = 0.750296

Measurements below this threshold were decoded as `1`, while measurements above it were decoded as `0`.

This initial test demonstrated successful CPU contention-based communication under the tested conditions.

## 4. Repeated Bit Duration Experiments

### Methodology

The message `10101010` was transmitted 11 times at each bit duration.

Both processes were pinned to logical CPU 0 using `taskset`.

The experiments used the same message and preamble to make results comparable across durations.

### Results

| Bit Duration    |       Trials |   Successful |      Bit Errors |          BER |
| --------------- | -----------: | -----------: | --------------: | -----------: |
| 200 ms          |           11 |           11 |            0/88 |           0% |
| 100 ms          |           11 |           11 |            0/88 |           0% |
| 50 ms           |           11 |           11 |            0/88 |           0% |
| **Total** | **33** | **33** | **0/264** | **0%** |

### Observations

All 33 transmissions were decoded successfully.

Reducing the bit duration from 200 ms to 50 ms did not produce any observed decoding errors under the baseline conditions.

However, the experiment used a single repeated message pattern. These results do not establish that all possible messages or operating conditions will produce the same accuracy.

## 5. Transmission Speed

The theoretical raw bit rate is calculated as:

Raw Bit Rate = 1000 / Bit Duration (ms)

The preamble introduces additional transmission overhead.

For an eight-bit message and an eight-bit preamble:

Theoretical Payload Rate = Message Bits / Total Transmission Time

### Results

| Duration | Raw Bit Rate | Theoretical Payload Rate |
| -------- | -----------: | -----------------------: |
| 200 ms   |     5 bits/s |               2.5 bits/s |
| 100 ms   |    10 bits/s |                 5 bits/s |
| 50 ms    |    20 bits/s |                10 bits/s |

The payload rates include preamble transmission time but exclude the initial synchronization waiting period, process startup overhead, and retransmissions.

### Observations

Reducing bit duration from 200 ms to 50 ms increases the theoretical raw bit rate by a factor of four.

No message decoding errors were observed during the repeated baseline experiments.

These values represent theoretical transmission rates. Actual end-to-end throughput has not yet been independently measured.

## 6. Message Pattern Experiments

### Objective

To verify that successful communication is not limited to the alternating message `10101010`.

### Methodology

Different binary patterns were transmitted using a 200 ms bit duration.

Each additional pattern was tested once.

### Results

| Message      | Purpose                  | Trials | Result  |
| ------------ | ------------------------ | -----: | ------- |
| `11111111` | Continuous busy activity |      1 | Success |
| `00000000` | Continuous idle activity |      1 | Success |
| `11110000` | Busy-to-idle transition  |      1 | Success |
| `00001111` | Idle-to-busy transition  |      1 | Success |
| `11001010` | Mixed message pattern    |      1 | Success |
| `1010`     | Four-bit message         |      1 | Success |

All six additional messages were decoded correctly.

The four-bit message demonstrated that communication also works with a shorter message length.

The sender and receiver implementations support variable-length binary messages of up to 1024 bits, although the full supported range has not been experimentally validated.

### Observations

The receiver successfully decoded consecutive `1`s, consecutive `0`s, transitions between busy and idle activity, and a mixed message pattern.

These results provide preliminary evidence that the channel supports different binary sequences.

Because each new pattern was tested only once, additional repeated experiments would be needed to characterize message-pattern reliability.

## 7. Overall Communication Results

- Total communication trials: 39
- Successful transmissions: 39
- Total message bits: 308
- Incorrect message bits: 0
- Observed message BER: 0%
- CPU configuration: Sender and receiver on logical CPU 0
- Added interference: None

The results demonstrate successful end-to-end communication under the tested baseline conditions.

The observed zero BER should not be interpreted as a guarantee of error-free communication in other scheduling environments.

### Experimental Evidence

Combined communication summary:

`results/baseline/baseline_combined_summary.csv`

Original repeated tests:

`results/baseline/standard_10101010/`

Additional message-pattern tests:

`results/baseline/<duration>ms_<message>/`

Historical exploratory tests:

`results/baseline/legacy_tests/`

Experiment runner:

`scripts/baseline.sh`

Analysis script:

`experiments/analyze_results.py`

## 8. Sender Timing Accuracy Experiments

### Objective

To evaluate how accurately the sender follows scheduled bit boundaries at durations of 50, 100, and 200 milliseconds.

### Methodology

The sender was executed independently, without a competing receiver.

It was pinned to logical CPU 0 using `taskset`.

The sender's optional `--timing` mode was enabled to record:

- Scheduled start timestamp
- Scheduled end timestamp
- Actual processing start timestamp
- Actual processing end timestamp
- Start timing error
- End timing error

The sender transmitted the preamble `11110000` followed by the message `10101010`.

Each run contained 16 bit intervals.

Each duration was tested 10 times.

| Duration        |       Trials |   Bit Records |
| --------------- | -----------: | ------------: |
| 200 ms          |           10 |           160 |
| 100 ms          |           10 |           160 |
| 50 ms           |           10 |           160 |
| **Total** | **30** | **480** |

### Timing Error Calculation

Start Error = Actual Start - Scheduled Start

End Error = Actual End - Scheduled End

Relative Average End Error (%) =
(Average End Error / Bit Duration) × 100

Timing measurements were stored in memory during transmission and printed after transmission completed to reduce instrumentation overhead during individual intervals.

### Results

| Duration | Avg Start Error | Avg End Error | Max End Error | Relative Avg Error |
| -------- | --------------: | ------------: | ------------: | -----------------: |
| 200 ms   |     0.285850 ms |   0.246362 ms |   0.926412 ms |             0.123% |
| 100 ms   |     0.211749 ms |   0.210907 ms |   0.834731 ms |             0.211% |
| 50 ms    |     0.243136 ms |   0.239125 ms |   0.823397 ms |             0.478% |

### Busy vs Idle Timing

| Duration | Avg Busy End Error | Avg Idle End Error |
| -------- | -----------------: | -----------------: |
| 200 ms   |        0.005265 ms |        0.487459 ms |
| 100 ms   |        0.006290 ms |        0.415523 ms |
| 50 ms    |        0.011232 ms |        0.467019 ms |

### Observations

1. All 480 recorded bit intervals had end errors below 1 ms.
2. Busy intervals generally produced much smaller end errors than idle intervals.
3. Busy waiting continuously checks `CLOCK_MONOTONIC`, allowing the sender to detect the deadline with relatively little delay when scheduled.
4. Idle intervals use `clock_nanosleep`, requiring the operating system to wake and schedule the sender again.
5. Average absolute end errors remained relatively similar across the three bit durations.
6. Relative average end error increased from approximately 0.123% at 200 ms to 0.478% at 50 ms.
7. This indicates that similar scheduling delays occupy a larger fraction of shorter bit intervals.
8. Absolute deadlines prevented ordinary execution delays from automatically shifting subsequent scheduled bit boundaries.

### Interpretation

The sender followed its scheduled deadlines with relatively small observed timing deviations under the tested sender-only conditions.

Busy intervals exhibited particularly small completion errors, whereas sleeping intervals experienced larger wake-up delays.

Although the absolute average end errors did not increase consistently as bit duration decreased, their relative size increased for shorter intervals.

This suggests shorter bit durations have less timing margin, although the baseline communication experiments did not exhibit decoding errors.

## 9. Timing Experiment Limitations

- The sender timing experiments did not include a competing receiver.
- All experiments were conducted in Ubuntu WSL2.
- Background processes and host scheduling activity were not fully controlled.
- Ten timing trials were performed per duration.
- The instrumentation introduces small measurement overhead.
- Start and end timestamps measure processing boundary deviations, not every CPU scheduling interruption.
- The results do not establish worst-case scheduling behavior.
- Timing results under additional contention may differ from sender-only results.

### Experimental Evidence

Raw timing logs:

`results/timing/50ms/`

`results/timing/100ms/`

`results/timing/200ms/`

Complete per-bit dataset:

`results/timing/sender_timing_all.csv`

Timing summary:

`results/timing/sender_timing_summary.csv`

Experiment runner:

`scripts/sender_timing.sh`

Analysis script:

`experiments/analyze_sender_timing.py`

## 10. Sender Timing Under CPU Contention

### Objective

To investigate whether running the receiver alongside the sender
on the same logical CPU affects the sender's timing accuracy.

### Experimental Setup

Two conditions were compared:

1. Sender alone on logical CPU 0.
2. Sender and receiver together on logical CPU 0.

Both conditions used:

- Ubuntu on WSL2
- Message: `10101010`
- Preamble: `11110000`
- Bit durations: 50, 100, and 200 ms
- 10 trials per duration
- Absolute timing using `CLOCK_MONOTONIC`
- Sender timing instrumentation enabled

The receiver was not deliberately introduced as a competing
workload during sender-only trials.

During contended trials, both processes were pinned to CPU 0
using `taskset`.

Each trial contained 16 bit intervals.

A total of 60 timing trials and 960 bit timing records
were collected across both conditions.

### Results

| Duration | Sender Alone Avg End Error | Sender + Receiver Avg End Error |   Difference |
| -------- | -------------------------: | ------------------------------: | -----------: |
| 200 ms   |                0.246362 ms |                     0.840597 ms | +0.594235 ms |
| 100 ms   |                0.210907 ms |                     0.781756 ms | +0.570849 ms |
| 50 ms    |                0.239125 ms |                     0.652424 ms | +0.413299 ms |

### Relative Timing Error Under Contention

| Duration | Avg End Error | Relative Error |
| -------- | ------------: | -------------: |
| 200 ms   |   0.840597 ms |         0.420% |
| 100 ms   |   0.781756 ms |         0.782% |
| 50 ms    |   0.652424 ms |         1.305% |

### Communication Reliability

All 30 sender–receiver timing trials successfully
decoded the transmitted message `10101010`.

- Successful transmissions: 30/30
- Message bits transmitted: 240
- Incorrect message bits: 0
- Observed BER: 0%

### Observations

1. Average sender end errors were higher when the receiver
   was running on the same logical CPU.
2. At 200 ms, average end error increased from approximately
   0.246 ms to 0.841 ms.
3. At 100 ms, average end error increased from approximately
   0.211 ms to 0.782 ms.
4. At 50 ms, average end error increased from approximately
   0.239 ms to 0.652 ms.
5. Although the absolute average end error under contention
   was lowest at 50 ms, the relative error was highest
   because the bit duration was shorter.
6. All contended communication trials decoded successfully
   despite the increased timing errors.

### Interpretation

The results show increased sender deadline deviations when
the sender and receiver competed for logical CPU 0.

This is consistent with scheduling contention delaying the
sender's execution near its scheduled deadlines.

However, the sender continued to use absolute deadlines,
and the observed timing deviations did not produce decoding
errors during the tested communication trials.

The results suggest that the channel tolerated these timing
deviations under the tested conditions.

### Limitations

- Experiments were performed on one WSL2 environment.
- Background system activity was not fully isolated.
- Only one message pattern was used.
- Ten trials were performed per duration and condition.
- Sender-only and contended trials were not randomized
  or interleaved.
- The experiments do not establish whether similar results
  would occur under heavier interference or CPU quotas.
- Measured timing errors represent processing boundary
  deviations rather than a complete scheduler trace.

### Experimental Evidence

Complete timing comparison:

`results/timing/sender_timing_comparison_all.csv`

Timing comparison summary:

`results/timing/sender_timing_comparison_summary.csv`

Contended experiment logs:

`results/timing/contended/`

Experiment runner:

`scripts/contended_timing.sh`

Analysis script:

`experiments/compare_sender_timing.py`



## 11. Measured Transmission Speed Analysis

### Objective

To compare theoretical transmission speed with actual
measured sender transmission duration under sender-only
and sender–receiver contention conditions.

### Methodology

Existing timing logs from 60 trials were analyzed.

For each trial, the analysis extracted:

- The scheduled transmission start timestamp
- The actual first-bit start timestamp
- The actual final-bit end timestamp
- The scheduled final-bit end timestamp

Each transmission contained an eight-bit preamble and
an eight-bit message.

Theoretical Payload Throughput =
Message Bits / Scheduled Transmission Duration

Measured Payload Throughput =
Message Bits / (Actual Final End - Scheduled Start)

The initial synchronization waiting period was excluded.

### Results

| Duration |      Theoretical |    Sender Alone | Sender + Receiver |
| -------- | ---------------: | --------------: | ----------------: |
| 200 ms   |  2.500000 bits/s | 2.499589 bits/s |   2.499923 bits/s |
| 100 ms   |  5.000000 bits/s | 4.998824 bits/s |   4.999657 bits/s |
| 50 ms    | 10.000000 bits/s | 9.994005 bits/s |   9.990655 bits/s |

### Observations

1. Measured transmission-window throughput remained close
   to theoretical throughput for all three durations.
2. Reducing bit duration from 200 ms to 50 ms increased
   theoretical payload throughput fourfold.
3. Running the receiver increased average sender deadline
   errors but did not substantially reduce throughput.
4. The use of absolute scheduled deadlines prevented
   small timing delays from automatically accumulating
   across subsequent bit intervals.
5. All 30 contended timing trials successfully decoded
   the transmitted message.

### Limitations

These values measure sender transmission-window throughput,
not complete process-launch-to-delivery latency.

The five-second synchronization waiting period is excluded.

Sender-only runs do not represent delivered communication
throughput because no receiver was present.

The findings apply to the tested eight-bit message and
preamble configuration.

### Experimental Evidence

Per-trial measurements:
`results/timing/throughput_all.csv`

Summary:
`results/timing/throughput_summary.csv`

Analysis script:
`experiments/analyze_throughput.py`

## 12. General Limitations

The experiments were performed on a single WSL2 environment.

CPU affinity restricted the sender and receiver to logical CPU 0 but did not guarantee exclusive use of that CPU.

Background system activity could still affect execution timing and receiver measurements.

The communication experiments did not deliberately introduce interference.

Most repeated communication trials used the same eight-bit alternating message.

Additional message patterns were tested only once.

The sender-only timing results cannot establish the timing accuracy of the sender under all possible CPU contention conditions.

The preliminary findings should therefore be interpreted within the tested environment and configurations.

## 13. Next Steps

- Complete measured transmission-speed and throughput analysis.
- Review sender implementation and experimental scripts.
- Integrate CPU affinity and cgroup quota experiments from Person 2.
- Integrate interference and legitimate workload experiments from Person 3.
- Combine experimental results and generate comparative graphs.
- Prepare the final research report and presentation.
- Review and merge the sender experiments into the GitHub main branch.
-
