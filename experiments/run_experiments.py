#!/usr/bin/env python3
"""
Karim (feature/interference): experiment runner — legitimate 1M-add workload under controlled
CPU interference (none/low/medium/high). Writes trial summaries + raw samples.

Does not modify or invoke teammate sender/receiver sources. Optional --probe-bin
can point at a separately built receiver binary for the same probe style.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROBE = ROOT / "bin" / "benchmark"
INTERFERENCE_SH = ROOT / "scripts" / "interference.sh"
RESULTS = ROOT / "results"
DEFAULT_SUMMARY = RESULTS / "experiment_runs.csv"
DEFAULT_RAW = RESULTS / "raw_samples.csv"

LEVEL_ORDER = ("none", "low", "medium", "high")

SUMMARY_FIELDS = [
    "trial_id",
    "recorded_at",
    "experiment",
    "interference_level",
    "interference_workers",
    "probe_bin",
    "benchmark_samples",
    "benchmark_avg_ms",
    "benchmark_min_ms",
    "benchmark_max_ms",
    "benchmark_std_ms",
    "benchmark_cv",
    "host",
    "notes",
]

RAW_FIELDS = [
    "trial_id",
    "interference_level",
    "sample_index",
    "execution_time_ms",
]


def ensure_built(probe: Path) -> None:
    if probe.is_file() and os.access(probe, os.X_OK):
        return
    if probe.resolve() != DEFAULT_PROBE.resolve():
        sys.exit(f"Probe not executable: {probe}")
    build = ROOT / "scripts" / "build.sh"
    subprocess.run(["bash", str(build)], check=True, cwd=ROOT)


def parse_probe_csv(stdout: str) -> list[float]:
    values: list[float] = []
    for line in stdout.splitlines():
        if line.startswith("sample,") or not line.strip():
            continue
        parts = line.split(",")
        if len(parts) == 2:
            values.append(float(parts[1]))
    return values


def run_probe(probe: Path, samples: int) -> list[float]:
    # Our benchmark: N --csv. Teammate receiver: N only (CSV on stdout).
    if probe.resolve() == DEFAULT_PROBE.resolve():
        cmd = [str(probe), str(samples), "--csv"]
    else:
        cmd = [str(probe), str(samples)]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    values = parse_probe_csv(proc.stdout)
    if not values:
        sys.exit(f"Probe produced no CSV samples: {probe}")
    return values


def interference_start(level: str) -> int:
    if level == "none":
        return 0
    proc = subprocess.run(
        ["bash", str(INTERFERENCE_SH), "start", level],
        check=True,
        capture_output=True,
        text=True,
    )
    m = re.search(r"workers=(\d+)", proc.stdout)
    return int(m.group(1)) if m else -1


def interference_stop() -> None:
    subprocess.run(
        ["bash", str(INTERFERENCE_SH), "stop"],
        capture_output=True,
        text=True,
    )


def load_csv(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def next_trial_id(rows: list[dict]) -> int:
    if not rows:
        return 1
    return max(int(r["trial_id"]) for r in rows) + 1


def sort_levels(levels: list[str]) -> list[str]:
    rank = {name: i for i, name in enumerate(LEVEL_ORDER)}
    return sorted(levels, key=lambda x: (rank.get(x, 100), x))


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def run_matrix(
    levels: list[str],
    samples: int,
    trials_per_level: int,
    settle_sec: float,
    summary_csv: Path,
    raw_csv: Path,
    probe: Path,
    fresh: bool,
) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    if fresh:
        for p in (summary_csv, raw_csv):
            if p.is_file():
                p.unlink()

    summary_rows = load_csv(summary_csv)
    raw_rows = load_csv(raw_csv)
    trial_id = next_trial_id(summary_rows)
    host = os.uname().nodename
    probe_label = str(probe)

    for level in sort_levels(levels):
        for _ in range(trials_per_level):
            workers = 0
            values: list[float] = []
            notes = ""
            try:
                workers = interference_start(level)
                if level != "none":
                    time.sleep(settle_sec)
                values = run_probe(probe, samples)
            except subprocess.CalledProcessError as exc:
                notes = f"error: {exc}"
            finally:
                if level != "none":
                    interference_stop()

            if values:
                avg = statistics.mean(values)
                vmin = min(values)
                vmax = max(values)
                stdev = statistics.pstdev(values) if len(values) > 1 else 0.0
                cv = (stdev / avg) if avg else float("nan")
                for i, ms in enumerate(values, start=1):
                    raw_rows.append(
                        {
                            "trial_id": trial_id,
                            "interference_level": level,
                            "sample_index": i,
                            "execution_time_ms": f"{ms:.6f}",
                        }
                    )
            else:
                avg = vmin = vmax = stdev = cv = float("nan")

            summary_rows.append(
                {
                    "trial_id": trial_id,
                    "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "experiment": "legitimate_workload_under_interference",
                    "interference_level": level,
                    "interference_workers": workers,
                    "probe_bin": probe_label,
                    "benchmark_samples": samples if values else 0,
                    "benchmark_avg_ms": f"{avg:.6f}",
                    "benchmark_min_ms": f"{vmin:.6f}",
                    "benchmark_max_ms": f"{vmax:.6f}",
                    "benchmark_std_ms": f"{stdev:.6f}",
                    "benchmark_cv": f"{cv:.6f}",
                    "host": host,
                    "notes": notes,
                }
            )
            print(
                f"trial {trial_id}: level={level} workers={workers} "
                f"avg={avg:.4f} ms std={stdev:.4f} ms cv={cv:.4f}"
            )
            trial_id += 1

    write_csv(summary_csv, SUMMARY_FIELDS, summary_rows)
    write_csv(raw_csv, RAW_FIELDS, raw_rows)
    print(f"Wrote {len(summary_rows)} trials -> {summary_csv}")
    print(f"Wrote {len(raw_rows)} samples -> {raw_csv}")


def parse_levels(s: str) -> list[str]:
    return [p.strip() for p in s.split(",") if p.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Karim: interference vs legitimate workload timing"
    )
    parser.add_argument("--levels", default="none,low,medium,high")
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--settle-sec", type=float, default=1.5)
    parser.add_argument("--output", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--raw-output", type=Path, default=DEFAULT_RAW)
    parser.add_argument(
        "--probe-bin",
        type=Path,
        default=DEFAULT_PROBE,
        help="Executable that prints sample,execution_time_ms CSV (default: bin/benchmark)",
    )
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()

    if shutil.which("bash") is None:
        sys.exit("Requires bash (WSL/Linux).")

    ensure_built(args.probe_bin)
    run_matrix(
        parse_levels(args.levels),
        args.samples,
        args.trials,
        args.settle_sec,
        args.output,
        args.raw_output,
        args.probe_bin,
        args.fresh,
    )


if __name__ == "__main__":
    main()