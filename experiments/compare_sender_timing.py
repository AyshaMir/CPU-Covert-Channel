
import csv
import statistics
from pathlib import Path

BASE = Path("results/timing")
DURATIONS = [200, 100, 50]
TRIALS = 10

all_records = []
summary_rows = []


def read_timing_file(path, duration, trial, condition):
    content = path.read_text()

    if "TIMING_RESULTS_BEGIN" not in content or \
       "TIMING_RESULTS_END" not in content:
        raise ValueError(f"Incomplete timing output: {path}")

    timing_text = content.split(
        "TIMING_RESULTS_BEGIN\n", 1
    )[1].split(
        "TIMING_RESULTS_END", 1
    )[0]

    reader = csv.DictReader(timing_text.strip().splitlines())
    rows = list(reader)

    if len(rows) != 16:
        raise ValueError(
            f"Expected 16 bit records in {path}, found {len(rows)}"
        )

    return [
        {
            "condition": condition,
            "duration_ms": duration,
            "trial": trial,
            "slot": int(row["slot"]),
            "bit": row["bit"],
            "start_error_ms": float(row["start_error_ms"]),
            "end_error_ms": float(row["end_error_ms"])
        }
        for row in rows
    ]


# Read both experimental conditions
for condition in ("alone", "contended"):
    for duration in DURATIONS:
        for trial in range(1, TRIALS + 1):

            if condition == "alone":
                filename = (
                    BASE / f"{duration}ms" /
                    f"trial{trial:02d}_sender.txt"
                )
            else:
                filename = (
                    BASE / "contended" / f"{duration}ms" /
                    f"trial{trial:02d}_sender.txt"
                )

            if not filename.exists():
                raise FileNotFoundError(filename)

            all_records.extend(
                read_timing_file(
                    filename, duration, trial, condition
                )
            )


# Calculate summary statistics
for condition in ("alone", "contended"):
    for duration in DURATIONS:

        subset = [
            row for row in all_records
            if row["condition"] == condition
            and row["duration_ms"] == duration
        ]

        end_errors = [r["end_error_ms"] for r in subset]
        start_errors = [r["start_error_ms"] for r in subset]

        busy_errors = [
            r["end_error_ms"] for r in subset
            if r["bit"] == "1"
        ]

        idle_errors = [
            r["end_error_ms"] for r in subset
            if r["bit"] == "0"
        ]

        summary_rows.append({
            "condition": condition,
            "duration_ms": duration,
            "trials": TRIALS,
            "bit_records": len(subset),
            "avg_start_error_ms": statistics.mean(start_errors),
            "avg_end_error_ms": statistics.mean(end_errors),
            "max_end_error_ms": max(end_errors),
            "avg_busy_end_error_ms": statistics.mean(busy_errors),
            "avg_idle_end_error_ms": statistics.mean(idle_errors),
            "relative_avg_end_error_percent":
                statistics.mean(end_errors) / duration * 100
        })


# Save a combined timing dataset
all_output = BASE / "sender_timing_comparison_all.csv"

with all_output.open("w", newline="") as file:
    writer = csv.DictWriter(
        file, fieldnames=all_records[0].keys()
    )
    writer.writeheader()
    writer.writerows(all_records)


# Save summary dataset
summary_output = BASE / "sender_timing_comparison_summary.csv"

with summary_output.open("w", newline="") as file:
    writer = csv.DictWriter(
        file, fieldnames=summary_rows[0].keys()
    )
    writer.writeheader()
    writer.writerows(summary_rows)


print("\nSENDER TIMING COMPARISON")
print("=" * 65)

for duration in DURATIONS:
    alone = next(
        row for row in summary_rows
        if row["condition"] == "alone"
        and row["duration_ms"] == duration
    )

    contended = next(
        row for row in summary_rows
        if row["condition"] == "contended"
        and row["duration_ms"] == duration
    )

    difference = (
        contended["avg_end_error_ms"] -
        alone["avg_end_error_ms"]
    )

    print(f"\nBit duration: {duration} ms")
    print(
        f"Sender alone:     {alone['avg_end_error_ms']:.6f} ms"
    )
    print(
        f"Sender+receiver:  {contended['avg_end_error_ms']:.6f} ms"
    )
    print(f"Difference:       {difference:+.6f} ms")

print("\nTotal bit records:", len(all_records))
print("Saved:", all_output)
print("Saved:", summary_output)
