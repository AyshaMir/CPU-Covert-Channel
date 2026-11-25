import csv
import re
import subprocess
import time
from pathlib import Path

MESSAGE = "10101010"
DURATION_MS = 200
TRIALS = 5

CONFIGS = [
    ("same_cpu", 0, 0, None),
    ("sibling_cpu", 0, 1, None),
    ("separate_cores", 0, 2, None),
    ("quota_75", 0, 0, 75),
    ("quota_50", 0, 0, 50),
    ("quota_25", 0, 0, 25),
    ("quota_10", 0, 0, 10),
]

Path("results/channel_logs").mkdir(parents=True, exist_ok=True)
output = "results/channel_reliability.csv"

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

            prefix = f"results/channel_logs/{name}_{trial}"
            Path(prefix + "_receiver.log").write_text(receiver_log)
            Path(prefix + "_sender.log").write_text(sender_log)

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
