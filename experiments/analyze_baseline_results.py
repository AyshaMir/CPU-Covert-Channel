import argparse
import csv
import re
from pathlib import Path

parser = argparse.ArgumentParser(
    description="Analyze CPU covert-channel baseline experiments"
)
parser.add_argument(
    "--base",
    type=Path,
    default=Path("results/baseline"),
    help="Directory containing baseline experiment logs"
)
args = parser.parse_args()

BASE = args.base
OUTPUT = BASE / "baseline_combined_summary.csv"

records = []


def extract(pattern, text):
    match = re.search(pattern, text)
    return match.group(1) if match else None


def analyze(receiver_file, sender_file, duration, message, trial):
    receiver_text = receiver_file.read_text()

    received = extract(
        r"Received message:\s*([01]+)", receiver_text
    )
    busy = extract(
        r"Busy reference:\s*([\d.]+)", receiver_text
    )
    idle = extract(
        r"Idle reference:\s*([\d.]+)", receiver_text
    )
    threshold = extract(
        r"Threshold:\s*([\d.]+)", receiver_text
    )

    if received is not None and len(received) == len(message):
        errors = sum(
            a != b for a, b in zip(message, received)
        )
        ber = errors / len(message)
        status = "success" if errors == 0 else "failure"
    else:
        errors = ""
        ber = ""
        status = "decode_failed"

    return {
        "trial": trial,
        "duration_ms": duration,
        "message_length": len(message),
        "cpu": 0,
        "transmitted": message,
        "received": received or "",
        "bit_errors": errors,
        "ber": ber,
        "busy_reference": busy or "",
        "idle_reference": idle or "",
        "threshold": threshold or "",
        "status": status,
        "receiver_log": str(receiver_file),
        "sender_log": str(sender_file)
    }


# 1. Original 33 verified baseline trials
for duration in (50, 100, 200):
    directory = BASE / "standard_10101010" / f"{duration}ms"

    for receiver_file in sorted(directory.glob("trial??_receiver_*.txt")):
        trial = int(receiver_file.name.split("_")[0][5:])

        sender_file = directory / (
            f"trial{trial:02d}_sender_{duration}ms.txt"
        )

        records.append(analyze(
            receiver_file, sender_file,
            duration, "10101010", trial
        ))


# 2. New message-specific experiments
for directory in sorted(BASE.iterdir()):
    if not directory.is_dir():
        continue

    match = re.fullmatch(r"(\d+)ms_([01]+)", directory.name)
    if not match:
        continue

    duration = int(match.group(1))
    message = match.group(2)

    # Supports both the old and new log locations
    for location in (directory, directory / "raw_logs"):
        for receiver_file in sorted(
            location.glob("trial??_receiver.txt")
        ):
            trial = int(receiver_file.stem.split("_")[0][5:])

            sender_file = location / f"trial{trial:02d}_sender.txt"

            records.append(analyze(
                receiver_file, sender_file,
                duration, message, trial
            ))


# 3. Export without overwriting previous summaries
fields = [
    "trial", "duration_ms", "message_length", "cpu",
    "transmitted", "received", "bit_errors", "ber",
    "busy_reference", "idle_reference", "threshold",
    "status", "receiver_log", "sender_log"
]

with OUTPUT.open("w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(records)


# 4. Print summary
print("\nCOMBINED BASELINE SUMMARY")
print("=" * 40)

for duration in (50, 100, 200):
    subset = [
        r for r in records
        if r["duration_ms"] == duration
    ]

    successful = sum(r["status"] == "success" for r in subset)

    print(f"{duration} ms: {successful}/{len(subset)} successful")

print("=" * 40)
print(f"Total trials: {len(records)}")
print(f"Saved: {OUTPUT}")
