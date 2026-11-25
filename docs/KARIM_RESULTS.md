# Karim — Results, Artifacts, and Remaining Scope

Branch: `feature/interference`
Member: **Karim** (8 GB laptop, WSL2 on `DESKTOP-2AJS0GP`, 4 logical CPUs)

---

## 1. Role vs teammates

| Member | Responsibility |
|--------|----------------|
| **Ayesha** | Sender: busy/idle bits, preamble `11110000`, slots **50/100/200 ms** |
| **Prabha** | Receiver decode, **affinity** / **cgroup quota** on her benchmark |
| **Karim** | **Interference**, legitimate benchmark, **automation**, BER/throughput/slowdown **graphs**, orchestrating sender+receiver **without editing their sources** |

---

## 2. What Karim shipped (code)

- `benchmark.c`, `interference.c`, `interference.sh` (`none/low/medium/high`)
- `build.sh` → compiles teammate sender/receiver into `bin/`
- `run_experiments.py` — workload slowdown matrix
- `run_channel_experiments.py` — channel + interference + **`--affinity same|separate`**, all slot sizes
- `run_research_matrix.sh` / `demo.sh full` — full evaluation run
- `collect_prabha_controls.sh` — runs Prabha scripts **in her tree**, copies benchmark CSVs (does not edit her code)
- `analyze_results.py` — workload + channel summaries and plots (50/100/200 ms)

`src/sender.c` / `src/receiver.c` on this branch: **empty stubs** (unchanged).

---

## 3. Research questions Karim contributes to

From the project brief:

1. **Does extra CPU load hurt normal apps?** → Yes (`experiment_runs.csv`, ~**2.3×** slowdown at `high` in latest matrix).
2. **Does interference affect the covert channel?** → Yes: under **same CPU**, decode fails often at `high`; under **separate CPUs** channel **did not decode** in this WSL setup (0/16 trials).
3. **BER vs slot duration (50/100/200 ms)?** → Recorded in `channel_summary.csv` (same CPU).
4. **Legitimate vs channel impact together?** → `benchmark_avg_ms` in `channel_trials.csv` per trial.

**Not fully answered by Karim alone:** cgroup **quota × covert channel** (Prabha’s `quota.sh` is benchmark-only; copied baselines under `results/prabha_controls/` when scripts run).

---

## 4. Latest research matrix (reproduce: `./scripts/run_research_matrix.sh`)

### Workload-only (interference × legitimate probe)

| Level | Mean slowdown (latest run) |
|-------|---------------------------|
| none | 1.00× |
| low | ~1.36× |
| medium | ~1.00× (WSL variance) |
| high | ~**2.30×** |

### Covert channel — **same CPU** (`taskset` CPU 0 for sender + receiver)

Message `10101010`, 2 trials per cell:

| Slot | none | low | medium | high |
|------|------|-----|--------|------|
| **50 ms** | 2/2 decode, BER 0 | 2/2 | 2/2 | **1/2** decode |
| **100 ms** | 2/2 | 2/2 | 2/2 | **0/2** |
| **200 ms** | 2/2 | 2/2 | 2/2 | **1/2** |

Interpretation: **fast slots tolerate light/medium interference** on this host; **high interference** breaks or blocks decode (aligns with brief goal “what affects reliability”).

### Covert channel — **separate CPUs** (sender CPU 0, receiver CPU 2)

100 ms and 200 ms, all interference levels: **0/16 successful decodes**.

Interpretation: **this scheduling covert channel needs shared CPU contention on our WSL setup** — separating sender/receiver prevents the receiver from seeing the signal (important finding for the report; matches Prabha’s earlier “same CPU slower” theme but **inverts** mitigation: separation **stops** this channel rather than improving BER).

### No-sender control

Receiver alone (`none` / `high`): **no** decoded payload (no false `10101010`).

---

## 5. Artifacts (committed on branch)

| File | Role |
|------|------|
| `experiment_runs.csv`, `raw_samples.csv`, `benchmark_slowdown_summary.csv` | Workload |
| `channel_trials.csv`, `channel_summary.csv`, `channel_metrics.csv` | Channel |
| `cpu_topology.txt` | Machine context |
| `results/prabha_controls/*.csv` | Prabha benchmark affinity/quota copies (when scripts succeed) |
| `results/plots/*.png` | Workload + channel figures (incl. **50 ms** plots) |

---

## 6. Backlog status

| Item | Status |
|------|--------|
| All slot durations 50/100/200 | **Done** (same-CPU matrix) |
| `medium` interference in channel + workload | **Done** |
| Same vs separate CPU for channel | **Done** (separate = no decode here) |
| Prabha control baselines (benchmark) | **Scripted** (`collect_prabha_controls.sh`; needs `stress-ng` + LF scripts to re-run fresh) |
| Quota × **covert channel** | **Open** (team / future wrapper) |
| Git merge all features to `main` | **Team** |
| Report / viva | **Team** |

---

## 7. One-liner for slides

**Karim measured interference-driven slowdown of a normal probe (~2.3× at high load), BER/decode success for `10101010` across 50–200 ms slots, and showed that pinning sender/receiver on different CPUs stops decoding entirely on WSL — while extra interference on a shared CPU can collapse the channel under heavy load.**