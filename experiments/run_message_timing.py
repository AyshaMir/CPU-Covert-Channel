
#!/usr/bin/env python3

import datetime
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MESSAGES = ["11111111", "00000000", "11001010"]
DURATIONS = [50, 100, 200]

def run_study(trials=1):
    run_id = datetime.datetime.now(
        datetime.timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    output_dir = (
        ROOT / "results" / "studies"
        / "additional_validation" / "sender_timing"
        / run_id
    )
    output_dir.mkdir(parents=True, exist_ok=False)

    for message in MESSAGES:
        for duration in DURATIONS:
            for trial in range(1, trials + 1):
                start_ns = time.monotonic_ns() + 5_000_000_000

                command = [
                    "taskset", "-c", "0",
                    str(ROOT / "bin" / "sender"),
                    message, str(duration), str(start_ns),
                    "--timing"
                ]

                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    capture_output=True,
                    text=True
                )

                log = output_dir / (
                    f"{message}_{duration}ms_trial{trial:02d}.txt"
                )
                log.write_text(
                    result.stdout + result.stderr,
                    encoding="utf-8"
                )

                if (
                    result.returncode != 0
                    or "TIMING_RESULTS_END" not in result.stdout
                ):
                    raise RuntimeError(
                        f"Timing trial failed: {log}"
                    )

                print(
                    f"{message} | {duration} ms | "
                    f"Trial {trial}: COMPLETE",
                    flush=True
                )

    print(f"\nResults saved to: {output_dir}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--trials", type=int, default=1
    )
    args = parser.parse_args()

    if args.trials < 1:
        parser.error("--trials must be positive")

    run_study(args.trials)
