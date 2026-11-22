
import csv
import statistics
from pathlib import Path

BASE = Path("results/timing")
DURATIONS = [200, 100, 50]
CONDITIONS = ["alone", "contended"]
TRIALS = 10
PREAMBLE_BITS = 8

records = []
summary = []


def read_trial(path, duration, trial, condition):
    content = path.read_text()

    if "TIMING_RESULTS_BEGIN" not in content:
        raise ValueError(f"Missing timing data: {path}")

    if "TIMING_RESULTS_END" not in content:
        raise ValueError(f"Incomplete timing data: {path}")

    timing_text = content.split(
        "TIMING_RESULTS_BEGIN", 1
    )[1].split(
        "TIMING_RESULTS_END", 1
    )[0].strip()

    rows = list(csv.DictReader(timing_text.splitlines()))

    if not rows:
        raise ValueError(f"No timing records: {path}")

    if len(rows) <= PREAMBLE_BITS:
        raise ValueError(f"No message bits found: {path}")

    # Confirm that all slots are present and in order.
    for expected_slot, row in enumerate(rows, start=1):
        if int(row["slot"]) != expected_slot:
            raise ValueError(f"Invalid slot sequence: {path}")

    message_bits = len(rows) - PREAMBLE_BITS

    first = rows[0]
    last = rows[-1]

    scheduled_start = int(first["scheduled_start_ns"])
    scheduled_end = int(last["scheduled_end_ns"])
    actual_start = int(first["actual_start_ns"])
    actual_end = int(last["actual_end_ns"])

    theoretical_seconds = (
        len(rows) * duration / 1000
    )

    # Time between actual first-bit start and final-bit end.
    active_seconds = (
        actual_end - actual_start
    ) / 1_000_000_000

    # Time from scheduled transmission start to actual completion.
    scheduled_window_seconds = (
        actual_end - scheduled_start
    ) / 1_000_000_000

    if active_seconds <= 0 or scheduled_window_seconds <= 0:
        raise ValueError(f"Invalid duration: {path}")

    # Verify that the recorded scheduled interval is correct.
    expected_ns = len(rows) * duration * 1_000_000

    if scheduled_end - scheduled_start != expected_ns:
        raise ValueError(f"Unexpected scheduled duration: {path}")

    theoretical_rate = message_bits / theoretical_seconds

    return {
        "condition": condition,
        "duration_ms": duration,
        "trial": trial,
        "message_bits": message_bits,
        "total_bits": len(rows),
        "theoretical_duration_s": theoretical_seconds,
        "active_duration_s": active_seconds,
        "scheduled_window_duration_s": scheduled_window_seconds,
        "theoretical_payload_bps": theoretical_rate,
        "active_payload_bps": message_bits / active_seconds,
        "scheduled_window_payload_bps":
            message_bits / scheduled_window_seconds,
        "initial_start_delay_ms":
            (actual_start - scheduled_start) / 1_000_000,
        "final_end_error_ms":
            (actual_end - scheduled_end) / 1_000_000
    }


# Read the existing experiment logs.
for condition in CONDITIONS:
    for duration in DURATIONS:
        for trial in range(1, TRIALS + 1):

            if condition == "alone":
                path = (
                    BASE / f"{duration}ms" /
                    f"trial{trial:02d}_sender.txt"
                )
            else:
                path = (
                    BASE / "contended" / f"{duration}ms" /
                    f"trial{trial:02d}_sender.txt"
                )

            if not path.exists():
                raise FileNotFoundError(path)

            records.append(
                read_trial(path, duration, trial, condition)
            )


# Summarize results for each condition and duration.
for condition in CONDITIONS:
    for duration in DURATIONS:

        subset = [
            r for r in records
            if r["condition"] == condition
            and r["duration_ms"] == duration
        ]

        def avg(field):
            return statistics.mean(r[field] for r in subset)

        theoretical = avg("theoretical_payload_bps")
        measured = avg("scheduled_window_payload_bps")

        summary.append({
            "condition": condition,
            "duration_ms": duration,
            "trials": len(subset),
            "avg_theoretical_duration_s":
                avg("theoretical_duration_s"),
            "avg_active_duration_s":
                avg("active_duration_s"),
            "avg_scheduled_window_duration_s":
                avg("scheduled_window_duration_s"),
            "theoretical_payload_bps": theoretical,
            "avg_active_payload_bps":
                avg("active_payload_bps"),
            "avg_scheduled_window_payload_bps": measured,
            "throughput_difference_bps":
                measured - theoretical,
            "avg_initial_start_delay_ms":
                avg("initial_start_delay_ms"),
            "avg_final_end_error_ms":
                avg("final_end_error_ms")
        })


# Save per-trial results.
BASE.mkdir(parents=True, exist_ok=True)

all_output = BASE / "throughput_all.csv"

with all_output.open("w", newline="") as file:
    writer = csv.DictWriter(
        file, fieldnames=records[0].keys()
    )
    writer.writeheader()
    writer.writerows(records)


# Save summary results.
summary_output = BASE / "throughput_summary.csv"

with summary_output.open("w", newline="") as file:
    writer = csv.DictWriter(
        file, fieldnames=summary[0].keys()
    )
    writer.writeheader()
    writer.writerows(summary)


# Print comparison.
print("\nTRANSMISSION SPEED ANALYSIS")
print("=" * 65)

for duration in DURATIONS:
    print(f"\nBit duration: {duration} ms")

    for condition in CONDITIONS:
        row = next(
            r for r in summary
            if r["condition"] == condition
            and r["duration_ms"] == duration
        )

        print(f"\n  Condition: {condition}")
        print(
            f"  Theoretical throughput: "
            f"{row['theoretical_payload_bps']:.6f} bits/s"
        )
        print(
            f"  Measured throughput:    "
            f"{row['avg_scheduled_window_payload_bps']:.6f} bits/s"
        )
        print(
            f"  Average duration:       "
            f"{row['avg_scheduled_window_duration_s']:.6f} s"
        )
        print(
            f"  Average start delay:    "
            f"{row['avg_initial_start_delay_ms']:.6f} ms"
        )

print("\nTotal trials:", len(records))
print("Saved:", all_output)
print("Saved:", summary_output)
