
#!/usr/bin/env python3

import argparse
import csv
import datetime
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MESSAGES = ["11111111", "00000000", "11001010"]
CONFIGS = [
    ("same_cpu", None),
    ("quota_25", 25),
    ("quota_10", 10),
]

DURATION_MS = 200
CPU = 0

FIELDS = [
    "configuration",
    "message",
    "trial",
    "duration_ms",
    "sender_quota",
    "received",
    "completed_decode",
    "exact_success",
    "bit_errors",
    "ber",
    "outcome",
    "sender_exit",
    "receiver_exit",
]


def run_study(trials):
    run_id = datetime.datetime.now(
        datetime.timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    output_dir = (
        ROOT / "results" / "studies"
        / "additional_validation" / "cpu_controls"
        / run_id
    )

    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=False)

    csv_path = output_dir / "channel_trials.csv"

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()

        for message in MESSAGES:
            for configuration, quota in CONFIGS:
                for trial in range(1, trials + 1):

                    start_ns = time.monotonic_ns() + 5_000_000_000

                    receiver_cmd = [
                        "taskset", "-c", str(CPU),
                        str(ROOT / "bin" / "receiver"),
                        str(len(message)),
                        str(DURATION_MS),
                        str(start_ns),
                    ]

                    sender_cmd = [
                        "taskset", "-c", str(CPU),
                        str(ROOT / "bin" / "sender"),
                        message,
                        str(DURATION_MS),
                        str(start_ns),
                    ]

                    if quota is not None:
                        sender_cmd = [
                            "systemd-run",
                            "--user",
                            "--scope",
                            "--quiet",
                            "-p", f"CPUQuota={quota}%",
                        ] + sender_cmd

                    receiver = subprocess.Popen(
                        receiver_cmd,
                        cwd=ROOT,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                    )

                    sender = subprocess.Popen(
                        sender_cmd,
                        cwd=ROOT,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                    )

                    try:
                        receiver_log, _ = receiver.communicate(
                            timeout=120
                        )
                        sender_log, _ = sender.communicate(
                            timeout=120
                        )
                    except subprocess.TimeoutExpired:
                        receiver.kill()
                        sender.kill()
                        receiver_log, _ = receiver.communicate()
                        sender_log, _ = sender.communicate()

                    prefix = (
                        f"{message}_{configuration}_trial{trial:02d}"
                    )

                    (log_dir / f"{prefix}_receiver.txt").write_text(
                        receiver_log, encoding="utf-8"
                    )

                    (log_dir / f"{prefix}_sender.txt").write_text(
                        sender_log, encoding="utf-8"
                    )

                    match = re.search(
                        r"Received message:\s*([01]+)",
                        receiver_log,
                    )

                    received = match.group(1) if match else ""
                    completed = len(received) == len(message)
                    exact = completed and received == message

                    bit_errors = (
                        sum(a != b for a, b in zip(message, received))
                        if completed else None
                    )

                    ber = (
                        bit_errors / len(message)
                        if completed else None
                    )

                    if sender.returncode != 0:
                        outcome = "sender_error"
                    elif receiver.returncode != 0 and not completed:
                        outcome = "receiver_error"
                    elif exact:
                        outcome = "success"
                    elif completed:
                        outcome = "bit_errors"
                    else:
                        outcome = "incomplete_decode"

                    writer.writerow({
                        "configuration": configuration,
                        "message": message,
                        "trial": trial,
                        "duration_ms": DURATION_MS,
                        "sender_quota": (
                            quota if quota is not None else "unrestricted"
                        ),
                        "received": received,
                        "completed_decode": int(completed),
                        "exact_success": int(
                            exact and sender.returncode == 0
                            and receiver.returncode == 0
                        ),
                        "bit_errors": bit_errors,
                        "ber": ber,
                        "outcome": outcome,
                        "sender_exit": sender.returncode,
                        "receiver_exit": receiver.returncode,
                    })

                    file.flush()

                    print(
                        f"{message} | {configuration} | "
                        f"Trial {trial}: {outcome} | "
                        f"received={received or 'NONE'}",
                        flush=True,
                    )

    print(f"\nResults saved to: {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=1)
    args = parser.parse_args()

    if args.trials < 1:
        parser.error("--trials must be positive")

    run_study(args.trials)
