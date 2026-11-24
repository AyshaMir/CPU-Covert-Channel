# Karim — Results, Artifacts, and Remaining Scope

Branch: `feature/interference`  
Member: **Karim** (8 GB laptop) — interference, legitimate benchmark, automation, graphs, **channel×interference orchestration**

---

## 1. Role (project brief)

Karim owns the **interference / normal-performance** axis and the automated measurement of how competing CPU load affects both:

1. **Legitimate programs** (slowdown), and  
2. The **covert channel** (BER / throughput / decode success), using Ayesha’s sender and Prabha’s receiver **without editing their source trees**.

---

## 2. What was implemented

| Asset | Purpose |
|-------|---------|
| `src/benchmark.c` / `src/interference.c` | Legitimate 1M-add probe + multi-worker CPU spinner |
| `scripts/build.sh` | Builds Karim tools **and** compiles teammate `sender`/`receiver` into `bin/` from sibling worktrees |
| `scripts/interference.sh` | `none\|low\|medium\|high` (+ optional `INTERFERENCE_CPU=N`) |
| `scripts/capture_topology.sh` | Host CPU topology → `results/cpu_topology.txt` |
| `scripts/demo.sh` | One-shot viva: build → workload → channel → analyze |
| `experiments/run_experiments.py` | Workload slowdown matrix |
| `experiments/run_channel_experiments.py` | Shared `start_ns`, sender+receiver, interference, optional `--no-sender` |
| `experiments/analyze_results.py` | Slowdown plots + channel BER/throughput/decode-success plots |

`src/sender.c` and `src/receiver.c` on this branch remain **empty stubs** (no overwrites of teammate modules).

---

## 3. Method (channel × interference)

```bash
./scripts/build.sh
python3 experiments/run_channel_experiments.py --fresh \
  --message 10101010 --durations 100,200 --levels none,low,high \
  --trials 3 --cpu 0 --lead-ms 5000
```

- Sender: `bin/sender` from `feature-sender-experiments`  
- Receiver: `bin/receiver` from `feature-receiver` (decodes; prints `Received message:`)  
- Both pinned with `taskset -c 0`  
- Interference workers started around each trial  
- After each trial, a short legitimate benchmark is recorded (**paired** slowdown)

No-sender control:

```bash
python3 experiments/run_channel_experiments.py --no-sender \
  --message 10101010 --durations 100 --levels none,high --trials 2 --cpu 0
```

---

## 4. Legitimate workload results (prior + still current)

| Level | Mean latency (ms) | Slowdown vs none |
|-------|------------------:|-----------------:|
| none | 2.705 | 1.00× |
| low | 3.255 | 1.20× |
| medium | 4.958 | 1.83× |
| high | 8.749 | **3.23×** |

Within-trial timing std rose from ~0.5 ms (`none`) to ~10.5 ms (`high`).

---

## 5. Channel × interference results (this run)

Message `10101010`, same CPU (`taskset -c 0`), 3 trials per cell (usable decoded rows only for BER).

| Slot | Level | Decode success | Mean BER (decoded trials) | Notes |
|------|-------|----------------|---------------------------|-------|
| 100 ms | none | 3/3 | 0.000 | Clean channel |
| 100 ms | low | 3/3 | 0.000 | Still reliable |
| 100 ms | high | 1/3 | 0.000 on the one decode | **2/3 failed to produce a decoded message** |
| 200 ms | none | 3/3 | 0.000 | Clean |
| 200 ms | low | 3/3 | **0.042** (one trial `10101011`) | Mild errors appear |
| 200 ms | high | **0/3** | n/a (treat as channel collapse) | No `Received message` lines |

Paired benchmark during channel trials: ~4–5 ms at `none`, ~6 ms at `low`, ~12–18 ms at `high`.

**No-sender control:** 4 trials (`none`/`high`) → **no** decoded payload (good: no false message string without a sender).

### Interpretation (report)

- Baseline covert channel works under light load (matches Ayesha’s clean BER).  
- **High interference** often prevents decode entirely — stronger disruption than soft bit flips.  
- Legitimate latency rises with the same interference levels — the cost of “noisy neighbor” load.  
- WSL2 noise remains a caveat; treat numbers as evidence of the effect, not a claim that interference “eliminates” covert channels.

---

## 6. Artifacts

| Path | Contents |
|------|----------|
| `results/experiment_runs.csv` / `raw_samples.csv` | Workload matrix |
| `results/benchmark_slowdown_summary.csv` | Aggregated slowdown |
| `results/channel_trials.csv` | Per-trial sent/decoded/BER/throughput + paired bench |
| `results/channel_summary.csv` | Decode rate + mean BER/throughput by level×slot |
| `results/cpu_topology.txt` | Host topology |
| `results/plots/benchmark_*.png` | Workload figures |
| `results/plots/channel_*.png` | BER, decode success, throughput, paired bench |

---

## 7. Backlog status

### Done on this branch

| ID | Item | Status |
|----|------|--------|
| B1 | Longer / multi-trial runs | **Done** (workload + channel matrices) |
| B2 | CPU topology capture | **Done** (`capture_topology.sh`) |
| B3 | Optional pin for interference | **Done** (`INTERFERENCE_CPU`) |
| B4 | Probe / teammate binaries | **Done** (`build.sh` → `bin/sender`,`bin/receiver`; `--probe-bin`) |
| B5 | Demo script | **Done** (`scripts/demo.sh`) |
| S1 | Shared `start_ns` orchestration | **Done** (`run_channel_experiments.py`) |
| S2 | Patterns under interference | **Done** (`10101010` × levels) |
| S3 | Durations × interference | **Done** (100 & 200 ms; 50 ms supported via CLI) |
| R1 | Decoded bits | **Unblocked** by Prabha; Karim parses `Received message:` |
| R2 | BER under interference | **Done** |
| R4 | No-sender control | **Done** |
| I2 | Channel CSV schema | **Done** (`channel_trials.csv`) |
| I4 | Paired BER + slowdown | **Done** (same trial records both) |

### Still open / team-level

| ID | Item | Why still open |
|----|------|----------------|
| R3 | Affinity/quota × channel × interference full matrix | Prabha’s `affinity.sh`/`quota.sh` measure **benchmark**, not the channel. Karim can wrap `taskset`/`systemd-run` further; a full quota×slot×interference grid is optional stretch / joint lab time |
| I1 | Single merged git tree | Team merge of three feature branches (not Karim-only) |
| I3 | Exhaustive matrix (all slots × affinity × quota × interference) | Needs joint schedule; tooling is ready to extend |
| — | More 50 ms trials / more repeats on quiet machine | Optional hardening for the report |

### Out of scope

- Editing teammate `sender.c` / `receiver.c` / `affinity.sh` / `quota.sh`  
- Claiming mitigations fully eliminate the covert channel  

---

## 8. Reproduce

```bash
cd feature-interference
./scripts/demo.sh
# or step-by-step commands in README.md
```

---

## 9. Report one-liner

**Karim shows that graded CPU interference both slows legitimate probes (~1.2–3.2×) and degrades the scheduling covert channel (decode failures under high load; occasional bit errors under low load), with BER/throughput and paired slowdown logged from the same automated trials.**
