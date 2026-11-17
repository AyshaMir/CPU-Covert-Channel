# Karim — Results, Artifacts, and Remaining Scope

Branch: `feature/interference`  
Member: **Karim** (8 GB laptop) — interference generator, legitimate-workload benchmark, experiment automation, BER/throughput helpers, graphs  

This document explains **what was measured**, **what each CSV/plot means**, **how that maps to Karim’s assigned work**, and **what is still left** (including dependencies on the sender and receiver).

---

## 1. What Karim is responsible for (project brief)

From the shared project goals, Karim owns the **interference / normal-performance** axis of the research question:

> Can two programs communicate secretly through CPU scheduling, and how do controls (and **competing CPU load**) affect that channel **without unnecessarily hurting normal programs**?

Karim’s deliverables from the brief / role split:

| Deliverable | Purpose in the overall project |
|-------------|--------------------------------|
| Configurable CPU interference | Extra competing load = “noisy neighbor” condition for channel and for normal apps |
| Legitimate workload benchmark | Measure how much **normal** programs slow down under that load |
| Python experiment automation | Repeatable trials → CSV logs |
| BER, throughput, slowdown metrics | Report numbers for reliability + performance cost |
| Graphs | Visual evidence for report / presentation |

Karim does **not** own: sender busy/idle encoding (Ayesha), receiver decoding / affinity / cgroup quotas (Prabha). Those stay on their branches; this branch keeps empty `sender.c` / `receiver.c` stubs.

---

## 2. What was checked (method)

### Environment

- Ubuntu on **WSL2**
- Host recorded in CSV: `DESKTOP-2AJS0GP`
- Tools built with `./scripts/build.sh` → `bin/benchmark`, `bin/interference`

### Probe (legitimate workload)

`src/benchmark.c` runs the same style of work Prabha’s receiver uses as a timing probe: **1,000,000 integer additions**, timed with `CLOCK_MONOTONIC`, result in **milliseconds**.

That is intentional: the covert channel works because the receiver’s loop **takes longer** when another process keeps the CPU busy. Karim measures the same kind of delay for a **benign** program under **controlled** background load (not the sender’s bit pattern yet).

### Interference levels

| Level | Workers (this machine) | Meaning |
|-------|------------------------|---------|
| `none` | 0 | Baseline — no interference load |
| `low` | 1 | Light competing CPU spin |
| `medium` | 2 (`nproc/2`) | Moderate contention |
| `high` | 4 (`nproc`) | Heavy contention |

Workers are busy-spin processes from `src/interference.c`, started/stopped by `scripts/interference.sh`.

### Trial design (run that produced these results)

```bash
./scripts/build.sh
python3 experiments/run_experiments.py --fresh --samples 20 --trials 3 --settle-sec 1.5
python3 experiments/analyze_results.py
```

| Parameter | Value | Why |
|-----------|------:|-----|
| Samples per trial | 20 | Matches Prabha’s early contention methodology (20 samples) |
| Trials per level | 3 | Averaging + SEM across repeats (WSL noise is high) |
| Levels | none, low, medium, high | Graded interference axis for the report |
| Settle time | 1.5 s | Let workers schedule before measuring |

**Total:** 4 levels × 3 trials × 20 samples = **12 trial rows**, **240 raw samples**.

### What was *not* checked yet

- Sending real covert bits with Ayesha’s sender while Karim’s interference runs  
- Decoding bits with Prabha’s receiver under interference  
- BER / throughput of the **channel** under interference  
- Combining interference with affinity / cgroup quotas  

Those require integration (see §7 backlog).

---

## 3. CSV files — what they contain

All under `results/` (gitignored; regenerate with the commands above).

### 3.1 `experiment_runs.csv` — one row per trial

Primary log from `run_experiments.py`.

| Column | Meaning |
|--------|---------|
| `trial_id` | 1…12 for this run |
| `recorded_at` | UTC timestamp |
| `experiment` | `legitimate_workload_under_interference` |
| `interference_level` | `none` / `low` / `medium` / `high` |
| `interference_workers` | Actual worker count started |
| `probe_bin` | Path to the benchmark binary used |
| `benchmark_samples` | Samples in that trial (20) |
| `benchmark_avg_ms` | Mean of those 20 sample times |
| `benchmark_min_ms` / `max_ms` | Extremes in the trial |
| `benchmark_std_ms` | Population std of the 20 samples (within-trial noise) |
| `benchmark_cv` | Coefficient of variation = std / mean (noise relative to mean) |
| `host` | Machine id |
| `notes` | Empty unless a trial failed |

**How to read it:** Compare `benchmark_avg_ms` and `benchmark_std_ms` across `interference_level`. Rising mean → slowdown of the normal program. Rising std/CV → more **timing jitter**, which is the same physical effect the receiver uses to sense bits — extra interference makes that jitter messier.

### 3.2 `raw_samples.csv` — one row per probe sample

| Column | Meaning |
|--------|---------|
| `trial_id` | Links to `experiment_runs.csv` |
| `interference_level` | Level for that trial |
| `sample_index` | 1…20 within the trial |
| `execution_time_ms` | Single 1M-add measurement |

**How to read it:** Used for the boxplot and for checking outliers (WSL spikes). Example: under `high`, individual samples can jump to tens of ms while quiet samples stay ~2.4 ms — scheduler contention is intermittent, not a flat delay.

### 3.3 `benchmark_slowdown_summary.csv` — aggregated for the report

Produced by `analyze_results.py` from the trial log.

| Column | Meaning |
|--------|---------|
| `interference_level` | Level |
| `trials` | Number of successful trials (3) |
| `mean_avg_ms` | Average of the three trial averages |
| `sem_across_trials_ms` | Standard error of the mean across trials |
| `mean_within_trial_std_ms` | Average of within-trial stds (timing noise) |
| `mean_cv` | Average CV |
| `baseline_none_ms` | Mean latency at `none` |
| `slowdown_vs_none` | `mean_avg_ms / baseline_none_ms` |

**Numbers from this run:**

| Level | Mean latency (ms) | SEM (ms) | Mean within-trial std (ms) | Slowdown vs none |
|-------|------------------:|---------:|---------------------------:|-----------------:|
| none | 2.705 | 0.117 | 0.493 | **1.00×** |
| low | 3.255 | 0.302 | 1.611 | **1.20×** |
| medium | 4.958 | 1.122 | 3.104 | **1.83×** |
| high | 8.749 | 1.206 | 10.458 | **3.23×** |

---

## 4. What the results mean

### Legitimate performance cost

Under **high** interference, the benign probe took about **3.2×** as long as with no interference load. Even **low** load was measurable (~**1.2×**).  

For the report: *extra CPU competitors hurt normal programs*. Any mitigation story later (quotas, affinity) must be compared against this cost — the brief asks whether controls disrupt the channel **without unnecessarily hurting normal performance**.

### Timing variance (link to the covert channel)

Within-trial standard deviation rose from ~**0.5 ms** (`none`) to ~**10.5 ms** (`high`).  

The receiver decodes bits by whether its work is “fast” or “slow.” Extra interference injects **random** delays on top of the sender’s intentional busy/idle pattern. Expectation after integration: **higher interference → higher BER** (and possibly lower usable throughput), at the same time as higher legitimate slowdown. That trade-off is **Karim’s** research angle.

### Caveats (do not over-claim)

- Measurements are on **WSL2**; host scheduling and VM noise inflate variance (also noted in Prabha’s early docs).
- This run measures **interference vs benchmark** on Karim’s branch, not yet **sender bit stream vs receiver decode**.
- Three trials are enough for a first reportable table; longer runs (especially on Prabha’s 16 GB machine) improve confidence.

---

## 5. What each plot means

Plots are in `results/plots/` (regenerate with `python3 experiments/analyze_results.py`).

| File | What it shows | How to explain it |
|------|---------------|-------------------|
| `benchmark_slowdown.png` | Bar of **slowdown vs none** by level | Cost to a normal program as interference rises (1.0 → ~3.2×). Main “performance impact” figure. |
| `benchmark_latency.png` | Mean probe time (ms) with **error bars (SEM)** across trials | Absolute latency; SEM shows trial-to-trial uncertainty under WSL. |
| `timing_variance.png` | Mean **within-trial std** by level | Scheduling noise / jitter. Ties interference load to decoding difficulty. |
| `latency_boxplot.png` | Distribution of all raw samples per level | Spread and outliers; shows contention is bursty, not constant. |

---

## 6. How this fulfills Karim’s task (so far)

| Required piece | Status | Evidence |
|----------------|--------|----------|
| Configurable CPU interference | **Done** | `src/interference.c`, `scripts/interference.sh` (`none`/`low`/`medium`/`high`) |
| Legitimate program benchmark | **Done** | `src/benchmark.c` (1M-add probe) |
| Automate experiments + collect results | **Done** | `experiments/run_experiments.py` → CSVs |
| Calculate performance slowdown | **Done** | `benchmark_slowdown_summary.csv` + plots |
| Graphs for scheduling interference | **Done** | Four PNGs under `results/plots/` |
| Analyze interference effect | **Done (partial)** | Documented here for **workload** impact; **channel BER** still needs sender+receiver |
| BER & throughput of the covert channel | **Helpers only** | `analyze_results.py` (`--sent-bits` / `--received-bits` / `--channel-csv`) — no real channel trials yet |

**Bottom line:** Karim’s **standalone** workstream (interference + normal-performance measurement + automation + graphs) is implemented and has real WSL numbers. The **integrated** covert-channel metrics under interference are the next phase and depend on teammates.

---

## 7. Backlog — what is left for Karim

### Can do on this branch without waiting (Karim only)

| # | Item | Notes |
|---|------|--------|
| B1 | Longer runs | e.g. `--trials 5` or `--samples 50` on the 8 GB laptop; reduce WSL noise in the report |
| B2 | Document CPU topology | Record `nproc`, `/proc/cpuinfo` summary next to results (8 GB vs Prabha 16 GB comparison later) |
| B3 | Optional affinity pin for interference workers | Only if team agrees; do **not** edit Prabha’s `affinity.sh` — call it or use `taskset` from the runner |
| B4 | Wire `--probe-bin` to a **built** copy of Prabha’s receiver binary | Same probe, their binary; **do not modify** their sources |
| B5 | Demo script | One command: build → matrix → analyze → open plots for viva |

### Blocked / dependent on Ayesha (sender)

| # | Item | Dependency |
|---|------|------------|
| S1 | Shared `start_ns` orchestration in the Python runner | Sender CLI: `sender <bits> <duration_ms> <start_ns>` already exists on `feature/sender` |
| S2 | Run known patterns (e.g. `10101010`) under `none`/`low`/`high` interference | Need built sender binary path; Karim must **not** copy sender into this branch |
| S3 | Throughput experiments across 50 / 100 / 200 ms slots **with interference** | Sender enforces those durations; Karim logs duration + interference level |

### Blocked / dependent on Prabha (receiver)

| # | Item | Dependency |
|---|------|------------|
| R1 | Decoded bit string per trial | Receiver today exports **timing samples**, not decoded bits — **decoding/calibration** must land on `feature/receiver` |
| R2 | BER under interference | Needs `sent_bits` (from experiment config) + `decoded_bits` (from receiver) |
| R3 | Channel trials with affinity / quota × interference | Prabha’s `affinity.sh` / `quota.sh` must be implemented and callable; Karim’s runner only orchestrates |
| R4 | No-sender control with receiver alone | Confirms false “bits” under interference (baseline for BER honesty) |

### Integration (all three)

| # | Item | Notes |
|---|------|--------|
| I1 | Merge `feature/sender`, `feature/receiver`, `feature/interference` into one runnable tree | Avoid overwriting teammate `src/` files |
| I2 | Agree CSV columns for channel rows | Suggested: `sent_bits`, `decoded_bits`, `bit_duration_ms`, `interference_level`, `affinity_mode`, `quota_pct`, `ber`, `throughput_bps`, `benchmark_avg_ms` |
| I3 | Full experiment matrix | Slot duration × same/separate CPU × quota × interference; Karim owns interference + slowdown columns |
| I4 | Answer the research question with **paired** numbers | Channel BER/throughput **and** legitimate slowdown under the same conditions |

### Explicitly out of Karim’s scope

- Changing `protocol.h` preamble / slot rules without team agreement  
- Implementing or rewriting `sender.c` / `receiver.c` on this branch  
- Owning cgroup / affinity implementation (Prabha)  
- Claiming that interference or quotas “eliminate” the covert channel (brief forbids that as success criterion)

---

## 8. How to reproduce these results

```bash
cd feature-interference   # or the WSL path to this worktree
./scripts/build.sh
python3 experiments/run_experiments.py --fresh --samples 20 --trials 3
python3 experiments/analyze_results.py
```

After sender/receiver integration (future):

```bash
python3 experiments/analyze_results.py \
  --sent-bits 10101010 \
  --received-bits <decoded> \
  --bit-duration-ms 100

# or a channel CSV with sent_bits,decoded_bits,bit_duration_ms:
python3 experiments/analyze_results.py --channel-csv results/channel_trials.csv
```

---

## 9. One-sentence summary for the report

**Karim shows that controlled CPU interference measurably slows a legitimate timing probe (~1.2×–3.2×) and sharply increases timing variance; the remaining work is to combine this load with the teammates’ sender/receiver so BER and throughput under interference can be measured alongside that performance cost.**