import csv
import re
import subprocess
import time
from pathlib import Path
import argparse
from datetime import datetime, timezone

MESSAGE = "10101010"
DURATION_MS = 200
parser = argparse.ArgumentParser(
    description="Test covert-channel reliability under CPU controls"
)
parser.add_argument("--trials", type=int, default=15)
parser.add_argument("--output-dir", type=Path, default=None)
args = parser.parse_args()

if args.trials < 1:
    parser.error("--trials must be positive")

TRIALS = args.trials

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUTPUT_DIR = args.output_dir or Path(
    f"results/studies/cpu_controls/channel_{RUN_ID}_{time.monotonic_ns()}"
)
LOG_DIR = OUTPUT_DIR / "channel_logs"

if OUTPUT_DIR.exists():
    parser.error(f"Output directory already exists: {OUTPUT_DIR}")

LOG_DIR.mkdir(parents=True)

CONFIGS = [
    ("same_cpu", 0, 0, None),
    ("sibling_cpu", 0, 1, None),
    ("separate_cores", 0, 2, None),
    ("quota_75", 0, 0, 75),
    ("quota_50", 0, 0, 50),
    ("quota_25", 0, 0, 25),
    ("quota_10", 0, 0, 10),
]

output = OUTPUT_DIR / "channel_reliability.csv"

with open(output, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "configuration", "trial", "sender_cpu", "receiver_cpu",
        "sender_quota", "sent", "received", "bit_errors",
        "ber", "outcome", "sender_exit", "receiver_exit"
    ])

    for name, receiver_cpu, sender_cpu, quota in CONFIGS:
        for trial in range(1, TRIALS + 1):
            start = time.clock_gettime_ns(time.CLOCK_MONOTONIC) + 5_000_000_000

            receiver_cmd = [
                "taskset", "-c", str(receiver_cpu),
                "./bin/receiver", str(len(MESSAGE)),
                str(DURATION_MS), str(start)
            ]

            sender_cmd = [
                "taskset", "-c", str(sender_cpu),
                "./bin/sender", MESSAGE,
                str(DURATION_MS), str(start)
            ]

            if quota is not None:
                sender_cmd = [
                    "systemd-run", "--user", "--scope", "--quiet",
                    "-p", f"CPUQuota={quota}%"
                ] + sender_cmd

            receiver = subprocess.Popen(
                receiver_cmd, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True
            )

            sender = subprocess.Popen(
                sender_cmd, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True
            )

            receiver_log, _ = receiver.communicate()
            sender_log, _ = sender.communicate()

            prefix = f"{name}_{trial}"
            (LOG_DIR / f"{prefix}_receiver.log").write_text(
                receiver_log, encoding="utf-8"
            )
            (LOG_DIR / f"{prefix}_sender.log").write_text(
                sender_log, encoding="utf-8"
            )

            match = re.search(
                r"Received message:\s*([01]+)", receiver_log
            )

            received = match.group(1) if match else ""
            bit_errors = ""
            ber = ""

            if sender.returncode != 0:
                outcome = "sender_error"
            elif received and receiver.returncode == 0:
                if len(received) == len(MESSAGE):
                    bit_errors = sum(
                        a != b for a, b in zip(MESSAGE, received)
                    )
                    ber = bit_errors / len(MESSAGE)
                    outcome = (
                        "success" if bit_errors == 0
                        else "bit_errors"
                    )
                else:
                    outcome = "length_mismatch"
            elif "Preamble validation failed" in receiver_log:
                outcome = "preamble_failed"
            else:
                outcome = "receiver_error"

            writer.writerow([
                name, trial, sender_cpu, receiver_cpu,
                quota if quota is not None else "unrestricted",
                MESSAGE, received, bit_errors, ber,
                outcome, sender.returncode, receiver.returncode
            ])
            f.flush()

            print(
                f"{name:16} trial={trial} "
                f"received={received or 'NONE':8} "
                f"BER={ber if ber != '' else 'N/A'} "
                f"outcome={outcome}",
                flush=True
            )

print(f"\nResults saved to {output}")
