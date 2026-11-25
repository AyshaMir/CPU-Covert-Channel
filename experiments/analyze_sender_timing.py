
import csv
import statistics
from pathlib import Path

BASE = Path("results/timing")
DURATIONS = [200, 100, 50]

records = []

for duration in DURATIONS:
    directory = BASE / f"{duration}ms"

    for trial in range(1, 11):
        filename = directory / f"trial{trial:02d}_sender.txt"

        if not filename.exists():
            print(f"Missing: {filename}")
            continue

        content = filename.read_text()

        if "TIMING_RESULTS_BEGIN" not in content or \
           "TIMING_RESULTS_END" not in content:
            print(f"Incomplete: {filename}")
            continue

        timing_text = content.split(
            "TIMING_RESULTS_BEGIN\n", 1
        )[1].split(
            "TIMING_RESULTS_END", 1
        )[0]

        reader = csv.DictReader(timing_text.strip().splitlines())

        for row in reader:
            records.append({
                "duration_ms": duration,
                "trial": trial,
                "slot": int(row["slot"]),
                "bit": row["bit"],
                "start_error_ms": float(row["start_error_ms"]),
                "end_error_ms": float(row["end_error_ms"])
            })


# Save all per-bit timing measurements
output = BASE / "sender_timing_all.csv"

with output.open("w", newline="") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=records[0].keys()
    )
    writer.writeheader()
    writer.writerows(records)


print("\nSENDER TIMING ANALYSIS")
print("=" * 55)

for duration in DURATIONS:
    subset = [
        r for r in records
        if r["duration_ms"] == duration
    ]

    end_errors = [r["end_error_ms"] for r in subset]
    start_errors = [r["start_error_ms"] for r in subset]

    print(f"\nBit duration: {duration} ms")
    print(f"Measurements: {len(subset)}")

    print(
        f"Average start error: "
        f"{statistics.mean(start_errors):.6f} ms"
    )

    print(
        f"Average end error: "
        f"{statistics.mean(end_errors):.6f} ms"
    )

    print(
        f"Maximum end error: "
        f"{max(end_errors):.6f} ms"
    )

    for bit in ("1", "0"):
        values = [
            r["end_error_ms"]
            for r in subset
            if r["bit"] == bit
        ]

        print(
            f"Average end error (bit {bit}): "
            f"{statistics.mean(values):.6f} ms"
        )

print("\nSaved:", output)


# Generate a summary CSV for the research report

summary_rows = []

for duration in DURATIONS:
    subset = [
        r for r in records
        if r["duration_ms"] == duration
    ]

    start_errors = [
        r["start_error_ms"] for r in subset
    ]

    end_errors = [
        r["end_error_ms"] for r in subset
    ]

    busy_errors = [
        r["end_error_ms"] for r in subset
        if r["bit"] == "1"
    ]

    idle_errors = [
        r["end_error_ms"] for r in subset
        if r["bit"] == "0"
    ]

    summary_rows.append({
        "duration_ms": duration,
        "trials": len(set(r["trial"] for r in subset)),
        "bit_records": len(subset),
        "avg_start_error_ms": statistics.mean(start_errors),
        "avg_end_error_ms": statistics.mean(end_errors),
        "max_end_error_ms": max(end_errors),
        "avg_busy_end_error_ms": statistics.mean(busy_errors),
        "avg_idle_end_error_ms": statistics.mean(idle_errors),
        "relative_avg_end_error_percent":
            statistics.mean(end_errors) / duration * 100
    })

summary_output = BASE / "sender_timing_summary.csv"

with summary_output.open("w", newline="") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=summary_rows[0].keys()
    )
    writer.writeheader()
    writer.writerows(summary_rows)

print("Timing summary saved:", summary_output)
