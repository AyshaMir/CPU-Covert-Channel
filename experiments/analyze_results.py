#!/usr/bin/env python3
"""
Karim (feature/interference): analysis — legitimate-workload slowdown under interference, timing
variance (relevant to covert-channel decoding noise), BER and throughput when
bit strings are available (post-integration with sender/receiver).
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "results" / "experiment_runs.csv"
DEFAULT_RAW = ROOT / "results" / "raw_samples.csv"
PLOTS = ROOT / "results" / "plots"
LEVEL_ORDER = ("none", "low", "medium", "high")


def bit_error_rate(sent: str, received: str) -> float:
    if len(sent) != len(received):
        raise ValueError("sent and received must be equal length")
    if not sent:
        return float("nan")
    return sum(a != b for a, b in zip(sent, received)) / len(sent)


def throughput_bps(bit_duration_ms: float, ber: float) -> float:
    if bit_duration_ms <= 0:
        return float("nan")
    return (1000.0 / bit_duration_ms) * max(0.0, 1.0 - ber)


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def level_key(name: str) -> tuple:
    try:
        return (LEVEL_ORDER.index(name), name)
    except ValueError:
        return (len(LEVEL_ORDER), name)


def summarize(rows: list[dict]) -> list[dict]:
    avgs: dict[str, list[float]] = defaultdict(list)
    stds: dict[str, list[float]] = defaultdict(list)
    cvs: dict[str, list[float]] = defaultdict(list)

    for r in rows:
        if r.get("notes"):
            continue
        try:
            avg = float(r["benchmark_avg_ms"])
            std = float(r["benchmark_std_ms"])
            cv = float(r.get("benchmark_cv", "nan"))
        except (KeyError, ValueError):
            continue
        if math.isnan(avg):
            continue
        level = r["interference_level"]
        avgs[level].append(avg)
        stds[level].append(std)
        if not math.isnan(cv):
            cvs[level].append(cv)

    baseline = statistics.mean(avgs["none"]) if avgs.get("none") else float("nan")
    out = []
    for level in sorted(avgs.keys(), key=level_key):
        mean_avg = statistics.mean(avgs[level])
        mean_std = statistics.mean(stds[level]) if stds[level] else float("nan")
        mean_cv = statistics.mean(cvs[level]) if cvs[level] else float("nan")
        trial_sem = (
            statistics.stdev(avgs[level]) / math.sqrt(len(avgs[level]))
            if len(avgs[level]) > 1
            else 0.0
        )
        out.append(
            {
                "interference_level": level,
                "trials": len(avgs[level]),
                "mean_avg_ms": mean_avg,
                "sem_across_trials_ms": trial_sem,
                "mean_within_trial_std_ms": mean_std,
                "mean_cv": mean_cv,
                "baseline_none_ms": baseline,
                "slowdown_vs_none": mean_avg / baseline
                if baseline and not math.isnan(baseline)
                else float("nan"),
            }
        )
    return out


def write_summary(summary: list[dict], path: Path) -> None:
    fields = [
        "interference_level",
        "trials",
        "mean_avg_ms",
        "sem_across_trials_ms",
        "mean_within_trial_std_ms",
        "mean_cv",
        "baseline_none_ms",
        "slowdown_vs_none",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in summary:
            w.writerow(
                {
                    "interference_level": row["interference_level"],
                    "trials": row["trials"],
                    "mean_avg_ms": f"{row['mean_avg_ms']:.6f}",
                    "sem_across_trials_ms": f"{row['sem_across_trials_ms']:.6f}",
                    "mean_within_trial_std_ms": f"{row['mean_within_trial_std_ms']:.6f}",
                    "mean_cv": f"{row['mean_cv']:.6f}",
                    "baseline_none_ms": f"{row['baseline_none_ms']:.6f}",
                    "slowdown_vs_none": f"{row['slowdown_vs_none']:.6f}",
                }
            )


def plot_results(summary: list[dict], raw_path: Path) -> None:
    import matplotlib.pyplot as plt

    PLOTS.mkdir(parents=True, exist_ok=True)
    levels = [r["interference_level"] for r in summary]
    slowdowns = [r["slowdown_vs_none"] for r in summary]
    means = [r["mean_avg_ms"] for r in summary]
    sems = [r["sem_across_trials_ms"] for r in summary]
    stds = [r["mean_within_trial_std_ms"] for r in summary]

    # 1) Slowdown (legitimate workload impact — report figure)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(levels, slowdowns, color="#1f4e79", edgecolor="black", linewidth=0.4)
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=1)
    ax.set_ylabel("Slowdown vs none")
    ax.set_xlabel("Interference level")
    ax.set_title("Legitimate workload slowdown under CPU interference")
    fig.tight_layout()
    p1 = PLOTS / "benchmark_slowdown.png"
    fig.savefig(p1, dpi=160)
    plt.close(fig)
    print(f"Wrote {p1}")

    # 2) Mean latency ± SEM across trials
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(levels, means, yerr=sems, capsize=4, color="#2e7d32", edgecolor="black", linewidth=0.4)
    ax.set_ylabel("Mean execution time (ms)")
    ax.set_xlabel("Interference level")
    ax.set_title("Probe latency vs interference (mean ± SEM across trials)")
    fig.tight_layout()
    p2 = PLOTS / "benchmark_latency.png"
    fig.savefig(p2, dpi=160)
    plt.close(fig)
    print(f"Wrote {p2}")

    # 3) Within-trial timing std (scheduling noise — channel reliability driver)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(levels, stds, color="#b45309", edgecolor="black", linewidth=0.4)
    ax.set_ylabel("Mean within-trial std (ms)")
    ax.set_xlabel("Interference level")
    ax.set_title("Timing variance under interference (decoding noise)")
    fig.tight_layout()
    p3 = PLOTS / "timing_variance.png"
    fig.savefig(p3, dpi=160)
    plt.close(fig)
    print(f"Wrote {p3}")

    # 4) Raw sample distributions if available
    if raw_path.is_file():
        by_level: dict[str, list[float]] = defaultdict(list)
        for r in load_rows(raw_path):
            by_level[r["interference_level"]].append(float(r["execution_time_ms"]))
        ordered = sorted(by_level.keys(), key=level_key)
        data = [by_level[k] for k in ordered]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.boxplot(data, tick_labels=ordered, showfliers=False)
        ax.set_ylabel("Execution time (ms)")
        ax.set_xlabel("Interference level")
        ax.set_title("Per-sample probe latency distribution")
        fig.tight_layout()
        p4 = PLOTS / "latency_boxplot.png"
        fig.savefig(p4, dpi=160)
        plt.close(fig)
        print(f"Wrote {p4}")


def load_channel_csv(path: Path) -> list[dict]:
    """Optional post-integration CSV with sent_bits, decoded_bits, bit_duration_ms."""
    return load_rows(path)


def analyze_channel(path: Path, out_csv: Path, summary_csv: Path) -> None:
    rows = load_channel_csv(path)
    out = []
    # Count attempted channel trials (with sender) for decode success rate
    attempts: dict[tuple[str, str], int] = defaultdict(int)
    successes: dict[tuple[str, str], int] = defaultdict(int)

    for r in rows:
        if r.get("experiment") == "no_sender_receiver_control":
            continue
        sent = r.get("sent_bits", "")
        recv = r.get("decoded_bits", "")
        aff = r.get("affinity_mode", "same_cpu") or "same_cpu"
        key = (aff, r.get("interference_level", ""), str(r.get("bit_duration_ms", "")))
        if sent:
            attempts[key] += 1
        try:
            duration = float(r.get("bit_duration_ms", "200"))
        except ValueError:
            duration = 200.0
        if not sent or not recv or len(sent) != len(recv):
            continue
        successes[key] += 1
        try:
            ber = float(r.get("ber", "nan"))
        except ValueError:
            ber = float("nan")
        if ber != ber:
            ber = bit_error_rate(sent, recv)
        try:
            tput = float(r.get("throughput_bps", "nan"))
        except ValueError:
            tput = float("nan")
        if tput != tput:
            tput = throughput_bps(duration, ber)
        out.append(
            {
                **{k: r.get(k, "") for k in r},
                "ber": f"{ber:.6f}",
                "throughput_bps": f"{tput:.4f}",
            }
        )

    if out:
        fields = list(out[0].keys())
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(out)
        print(f"Wrote channel metrics {out_csv}")
    else:
        print(f"No fully decoded channel rows in {path}")

    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for r in out:
        aff = r.get("affinity_mode", "same_cpu") or "same_cpu"
        groups[(aff, r.get("interference_level", ""), str(r.get("bit_duration_ms", "")))].append(r)

    def sort_key(k: tuple[str, str, str]) -> tuple:
        return (k[0], level_key(k[1]), k[2])

    all_keys = sorted(set(attempts.keys()) | set(groups.keys()), key=sort_key)
    summary_rows = []
    for key in all_keys:
        affinity_mode, level, duration = key
        items = groups.get(key, [])
        n_att = attempts.get(key, 0)
        n_ok = successes.get(key, 0)
        decode_rate = (n_ok / n_att) if n_att else float("nan")
        if items:
            bers = [float(i["ber"]) for i in items]
            tputs = [float(i["throughput_bps"]) for i in items]
            mean_ber = statistics.mean(bers)
            mean_tput = statistics.mean(tputs)
        else:
            mean_ber = float("nan")
            mean_tput = 0.0
        benches = []
        for i in items:
            try:
                v = float(i.get("benchmark_avg_ms", "nan"))
            except ValueError:
                v = float("nan")
            if v == v:
                benches.append(v)
        # Also pull benchmark from failed decode rows in raw CSV
        if not benches:
            for r in rows:
                if (
                    r.get("interference_level") == level
                    and str(r.get("bit_duration_ms", "")) == duration
                    and r.get("sent_bits")
                ):
                    try:
                        v = float(r.get("benchmark_avg_ms", "nan"))
                    except ValueError:
                        continue
                    if v == v:
                        benches.append(v)
        summary_rows.append(
            {
                "affinity_mode": affinity_mode,
                "interference_level": level,
                "bit_duration_ms": duration,
                "trials_attempted": n_att,
                "trials_decoded": n_ok,
                "decode_success_rate": f"{decode_rate:.6f}" if decode_rate == decode_rate else "nan",
                "mean_ber": f"{mean_ber:.6f}" if mean_ber == mean_ber else "nan",
                "mean_throughput_bps": f"{mean_tput:.4f}",
                "mean_benchmark_avg_ms": f"{statistics.mean(benches):.6f}"
                if benches
                else "nan",
            }
        )

    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "affinity_mode",
            "interference_level",
            "bit_duration_ms",
            "trials_attempted",
            "trials_decoded",
            "decode_success_rate",
            "mean_ber",
            "mean_throughput_bps",
            "mean_benchmark_avg_ms",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(summary_rows)
    print(f"Wrote channel summary {summary_csv}")
    for row in summary_rows:
        print(
            f"  affinity={row.get('affinity_mode','')} level={row['interference_level']} "
            f"slot={row['bit_duration_ms']}ms decode={row['trials_decoded']}/{row['trials_attempted']} "
            f"BER={row['mean_ber']} tput={row['mean_throughput_bps']} "
            f"bench_ms={row['mean_benchmark_avg_ms']}"
        )

    if summary_rows:
        plot_channel(summary_rows)


def plot_channel(summary_rows: list[dict]) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib missing; skip channel plots", file=sys.stderr)
        return

    PLOTS.mkdir(parents=True, exist_ok=True)
    # Prefer one duration for the main BER bar (most common / first)
    durations = sorted({r["bit_duration_ms"] for r in summary_rows})
    for duration in durations:
        subset = [
            r
            for r in summary_rows
            if str(r["bit_duration_ms"]) == str(duration) and r.get("affinity_mode") == "same_cpu"
        ]
        if not subset:
            subset = [r for r in summary_rows if str(r["bit_duration_ms"]) == str(duration)]
        subset = sorted(subset, key=lambda r: level_key(r["interference_level"]))
        levels = [r["interference_level"] for r in subset]

        def ffloat(row: dict, key: str) -> float:
            try:
                return float(row.get(key, "nan"))
            except ValueError:
                return float("nan")

        # Treat failed decode as BER=1.0 for plotting completeness
        bers = []
        for r in subset:
            b = ffloat(r, "mean_ber")
            if b != b:
                b = 1.0 if ffloat(r, "decode_success_rate") == 0.0 else float("nan")
            bers.append(0.0 if b != b else b)
        decode_rates = [ffloat(r, "decode_success_rate") for r in subset]
        tputs = [ffloat(r, "mean_throughput_bps") for r in subset]
        benches = [ffloat(r, "mean_benchmark_avg_ms") for r in subset]

        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.bar(levels, bers, color="#9a3412", edgecolor="black", linewidth=0.4)
        ax.set_ylabel("Mean BER (decode fail → 1.0)")
        ax.set_xlabel("Interference level")
        ax.set_title(f"Covert-channel BER vs interference ({duration} ms slots)")
        ax.set_ylim(0, 1.05)
        fig.tight_layout()
        p = PLOTS / f"channel_ber_{duration}ms.png"
        fig.savefig(p, dpi=160)
        plt.close(fig)
        print(f"Wrote {p}")

        if any(d == d for d in decode_rates):
            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.bar(
                levels,
                [0.0 if d != d else d for d in decode_rates],
                color="#7c2d12",
                edgecolor="black",
                linewidth=0.4,
            )
            ax.set_ylabel("Decode success rate")
            ax.set_xlabel("Interference level")
            ax.set_title(f"Decode success vs interference ({duration} ms slots)")
            ax.set_ylim(0, 1.05)
            fig.tight_layout()
            p = PLOTS / f"channel_decode_success_{duration}ms.png"
            fig.savefig(p, dpi=160)
            plt.close(fig)
            print(f"Wrote {p}")

        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.bar(levels, tputs, color="#1d4ed8", edgecolor="black", linewidth=0.4)
        ax.set_ylabel("Mean effective throughput (bits/s)")
        ax.set_xlabel("Interference level")
        ax.set_title(f"Effective throughput vs interference ({duration} ms slots)")
        fig.tight_layout()
        p = PLOTS / f"channel_throughput_{duration}ms.png"
        fig.savefig(p, dpi=160)
        plt.close(fig)
        print(f"Wrote {p}")

        if any(b == b for b in benches):
            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.bar(levels, benches, color="#166534", edgecolor="black", linewidth=0.4)
            ax.set_ylabel("Paired benchmark avg (ms)")
            ax.set_xlabel("Interference level")
            ax.set_title(
                f"Legitimate probe latency during channel trials ({duration} ms)"
            )
            fig.tight_layout()
            p = PLOTS / f"channel_paired_benchmark_{duration}ms.png"
            fig.savefig(p, dpi=160)
            plt.close(fig)
            print(f"Wrote {p}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument(
        "--summary",
        type=Path,
        default=ROOT / "results" / "benchmark_slowdown_summary.csv",
    )
    parser.add_argument("--sent-bits")
    parser.add_argument("--received-bits")
    parser.add_argument("--bit-duration-ms", type=float, default=200.0)
    parser.add_argument(
        "--channel-csv",
        type=Path,
        help="CSV from run_channel_experiments.py (sent_bits, decoded_bits, …)",
    )
    parser.add_argument(
        "--skip-workload",
        action="store_true",
        help="Only analyze --channel-csv (skip experiment_runs)",
    )
    args = parser.parse_args()

    if not args.skip_workload:
        if not args.input.is_file():
            sys.exit(f"Missing {args.input}")

        rows = load_rows(args.input)
        summary = summarize(rows)
        write_summary(summary, args.summary)
        print(f"Wrote {args.summary}")
        for row in summary:
            print(
                f"  {row['interference_level']}: "
                f"mean={row['mean_avg_ms']:.3f}±{row['sem_across_trials_ms']:.3f} ms "
                f"std={row['mean_within_trial_std_ms']:.3f} ms "
                f"slowdown={row['slowdown_vs_none']:.3f}x"
            )

        try:
            plot_results(summary, args.raw)
        except ImportError:
            sys.exit("matplotlib required: python3 -m pip install matplotlib")

    if args.sent_bits and args.received_bits:
        ber = bit_error_rate(args.sent_bits, args.received_bits)
        tput = throughput_bps(args.bit_duration_ms, ber)
        print(f"BER={ber:.6f}  throughput={tput:.4f} bits/s  slot={args.bit_duration_ms} ms")

    channel_path = args.channel_csv
    if channel_path is None:
        default_ch = ROOT / "results" / "channel_trials.csv"
        if default_ch.is_file():
            channel_path = default_ch
    if channel_path:
        analyze_channel(
            channel_path,
            ROOT / "results" / "channel_metrics.csv",
            ROOT / "results" / "channel_summary.csv",
        )


if __name__ == "__main__":
    main()