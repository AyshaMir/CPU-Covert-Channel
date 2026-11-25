
#!/usr/bin/env python3
"""Analyze CPU affinity, CPU quotas, and channel reliability."""

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


parser = argparse.ArgumentParser()
parser.add_argument("--run-dir", type=Path, required=True)
args = parser.parse_args()

RUN_DIR = args.run_dir
PLOTS_DIR = RUN_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved: {path}")


def summarize_performance(filename, group_column, baseline_name):
    rows = read_csv(RUN_DIR / filename)
    groups = defaultdict(list)

    for row in rows:
        groups[row[group_column]].append(float(row["average_ms"]))

    if baseline_name not in groups:
        raise ValueError(f"Missing baseline: {baseline_name}")

    baseline = statistics.mean(groups[baseline_name])
    summaries = []

    for name, values in groups.items():
        mean = statistics.mean(values)

        summaries.append({
            group_column: name,
            "trials": len(values),
            "mean_ms": round(mean, 6),
            "std_ms": (
                round(statistics.stdev(values), 6)
                if len(values) > 1 else ""
            ),
            "slowdown": round(mean / baseline, 6),
        })

    output = RUN_DIR / filename.replace(".csv", "_summary.csv")

    write_csv(
        output,
        summaries,
        [group_column, "trials", "mean_ms", "std_ms", "slowdown"]
    )

    names = [row[group_column] for row in summaries]
    slowdowns = [row["slowdown"] for row in summaries]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(names, slowdowns)
    ax.axhline(1.0, linestyle="--", color="gray")
    ax.set_xlabel(group_column.replace("_", " ").title())
    ax.set_ylabel("Slowdown relative to baseline")
    ax.set_title(filename.replace(".csv", "").replace("_", " ").title())
    fig.tight_layout()

    plot_path = PLOTS_DIR / filename.replace(".csv", "_slowdown.png")
    fig.savefig(plot_path, dpi=160)
    plt.close(fig)

    print(f"Saved: {plot_path}")


def summarize_channel():
    path = RUN_DIR / "channel" / "channel_reliability.csv"
    rows = read_csv(path)

    groups = defaultdict(list)

    for row in rows:
        groups[row["configuration"]].append(row)

    summaries = []

    for configuration, trials in groups.items():
        attempts = len(trials)
        exact_successes = sum(
            row["outcome"] == "success"
            for row in trials
        )

        completed = [
            row for row in trials
            if row["received"]
            and len(row["received"]) == len(row["sent"])
            and row["sender_exit"] == "0"
            and row["receiver_exit"] == "0"
        ]

        bers = [
            sum(a != b for a, b in zip(row["sent"], row["received"]))
            / len(row["sent"])
            for row in completed
            if row["sent"]
        ]

        summaries.append({
            "configuration": configuration,
            "attempts": attempts,
            "completed_decodes": len(completed),
            "exact_successes": exact_successes,
            "decode_success_rate": round(len(completed) / attempts, 6),
            "message_success_rate": round(exact_successes / attempts, 6),
            "mean_ber": (
                round(statistics.mean(bers), 6)
                if bers else "N/A"
            ),
        })

    output = RUN_DIR / "channel_reliability_summary.csv"

    write_csv(
        output,
        summaries,
        [
            "configuration",
            "attempts",
            "completed_decodes",
            "exact_successes",
            "decode_success_rate",
            "message_success_rate",
            "mean_ber",
        ]
    )

    names = [row["configuration"] for row in summaries]
    rates = [row["message_success_rate"] * 100 for row in summaries]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(names, rates)
    ax.set_xlabel("CPU configuration")
    ax.set_ylabel("Exact-message success rate (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Covert-Channel Reliability Under CPU Controls")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()

    plot_path = PLOTS_DIR / "channel_reliability.png"
    fig.savefig(plot_path, dpi=160)
    plt.close(fig)

    print(f"Saved: {plot_path}")


def main():
    summarize_performance(
        "affinity_performance.csv",
        "configuration",
        "baseline"
    )

    summarize_performance(
        "quota_performance.csv",
        "quota",
        "unrestricted"
    )

    summarize_channel()

    print("\nCPU controls analysis completed successfully!")


if __name__ == "__main__":
    main()
