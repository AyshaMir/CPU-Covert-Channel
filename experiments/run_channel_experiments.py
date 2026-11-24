#!/usr/bin/env python3
"""
Karim: run Ayesha sender + Prabha receiver under controlled interference.
Builds nothing into teammate trees — uses bin/sender and bin/receiver from
scripts/build.sh (compiled from sibling worktree sources).

Writes results/channel_trials.csv for BER / throughput analysis.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
DEFAULT_CSV = RESULTS / "channel_trials.csv"
INTERFERENCE_SH = ROOT / "scripts" / "interference.sh"
SENDER = ROOT / "bin" / "sender"
RECEIVER = ROOT / "bin" / "receiver"
BENCHMARK = ROOT / "bin" / "benchmark"

RECEIVED_RE = re.compile(r"Received message:\s*([01]+)")

CHANNEL_FIELDS = [
    "trial_id",
    "recorded_at",
    "experiment",
    "sent_bits",
    "decoded_bits",
    "bit_duration_ms",
    "interference_level",
    "interference_workers",
    "affinity_cpu",
    "bit_errors",
    "ber",
    "throughput_bps",
    "benchmark_avg_ms",
    "sender_rc",
    "receiver_rc",
    "host",
    "notes",
]


def bit_error_rate(sent: str, received: str) -> tuple[int, float]:
    if not sent or len(sent) != len(received):
        return -1, float("nan")
    errors = sum(a != b for a, b in zip(sent, received))
    return errors, errors / len(sent)


def throughput_bps(duration_ms: float, ber: float) -> float:
    if duration_ms <= 0 or ber != ber:  # NaN check
        return float("nan")
    return (1000.0 / duration_ms) * max(0.0, 1.0 - ber)


def ensure_channel_bins() -> None:
    build = ROOT / "scripts" / "build.sh"
    if not SENDER.is_file() or not RECEIVER.is_file():
        subprocess.run(["bash", str(build)], check=True, cwd=ROOT)
    if not SENDER.is_file() or not RECEIVER.is_file():
        sys.exit(
            "Missing bin/sender or bin/receiver. "
            "Ensure sibling teammate trees exist, then: ./scripts/build.sh"
        )


def interference_start(level: str) -> int:
    if level == "none":
        return 0
    proc = subprocess.run(
        ["bash", str(INTERFERENCE_SH), "start", level],
        check=True,
        capture_output=True,
        text=True,
    )
    m = re.search(r"workers=(\d+)", proc.stdout)
    return int(m.group(1)) if m else -1


def interference_stop() -> None:
    subprocess.run(
        ["bash", str(INTERFERENCE_SH), "stop"],
        capture_output=True,
        text=True,
    )


def parse_received(text: str) -> str:
    m = RECEIVED_RE.search(text)
    return m.group(1) if m else ""


def run_benchmark_quick(samples: int = 10) -> float:
    if not BENCHMARK.is_file():
        return float("nan")
    proc = subprocess.run(
        [str(BENCHMARK), str(samples), "--csv"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return float("nan")
    vals = []
    for line in proc.stdout.splitlines():
        if line.startswith("sample,") or not line.strip():
            continue
        parts = line.split(",")
        if len(parts) == 2:
            vals.append(float(parts[1]))
    return sum(vals) / len(vals) if vals else float("nan")


def prefix_taskset(cmd: list[str], cpu: int | None) -> list[str]:
    if cpu is None:
        return cmd
    if shutil.which("taskset") is None:
        return cmd
    return ["taskset", "-c", str(cpu), *cmd]


def run_one_trial(
    *,
    message: str,
    duration_ms: int,
    lead_ms: int,
    interference_level: str,
    affinity_cpu: int | None,
    with_sender: bool,
    log_dir: Path,
    trial_tag: str,
) -> dict:
    workers = 0
    notes = ""
    sender_rc = ""
    receiver_rc = ""
    decoded = ""
    bench_ms = float("nan")

    try:
        workers = interference_start(interference_level)
        if interference_level != "none":
            time.sleep(1.0)

        start_ns = time.monotonic_ns() + lead_ms * 1_000_000
        msg_len = str(len(message))

        recv_cmd = prefix_taskset(
            [str(RECEIVER), msg_len, str(duration_ms), str(start_ns)],
            affinity_cpu,
        )
        recv_log = log_dir / f"{trial_tag}_receiver.txt"
        send_log = log_dir / f"{trial_tag}_sender.txt"

        recv_proc = subprocess.Popen(
            recv_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=ROOT,
        )

        if with_sender:
            send_cmd = prefix_taskset(
                [str(SENDER), message, str(duration_ms), str(start_ns)],
                affinity_cpu,
            )
            send_proc = subprocess.run(
                send_cmd,
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            sender_rc = str(send_proc.returncode)
            send_log.write_text(
                send_proc.stdout + send_proc.stderr, encoding="utf-8"
            )
        else:
            sender_rc = "skipped"
            send_log.write_text("no-sender control\n", encoding="utf-8")
            # Wait for receiver slot window to finish
            preamble = 8
            total_slots = preamble + len(message)
            wait_s = (lead_ms / 1000.0) + (total_slots * duration_ms / 1000.0) + 1.0
            time.sleep(wait_s)

        try:
            out, _ = recv_proc.communicate(timeout=lead_ms / 1000.0 + 120.0)
        except subprocess.TimeoutExpired:
            recv_proc.kill()
            out, _ = recv_proc.communicate()
            notes = "receiver_timeout"

        receiver_rc = str(recv_proc.returncode)
        recv_log.write_text(out or "", encoding="utf-8")
        decoded = parse_received(out or "")

        # Paired legitimate slowdown under same interference
        bench_ms = run_benchmark_quick(10)

    except subprocess.CalledProcessError as exc:
        notes = f"error: {exc}"
    finally:
        if interference_level != "none":
            interference_stop()

    if with_sender and decoded:
        errors, ber = bit_error_rate(message, decoded)
    elif with_sender and not decoded:
        errors, ber = -1, float("nan")
        notes = (notes + "; ").lstrip("; ") + "no_decoded_bits"
    else:
        # No-sender control: record whatever was decoded for false-positive analysis
        errors, ber = (-1, float("nan")) if not decoded else bit_error_rate(
            "0" * len(decoded), decoded
        )
        notes = (notes + "; ").lstrip("; ") + "no_sender_control"

    tput = throughput_bps(float(duration_ms), ber) if ber == ber else float("nan")

    return {
        "sent_bits": message if with_sender else "",
        "decoded_bits": decoded,
        "bit_duration_ms": duration_ms,
        "interference_level": interference_level,
        "interference_workers": workers,
        "affinity_cpu": "" if affinity_cpu is None else affinity_cpu,
        "bit_errors": errors,
        "ber": ber,
        "throughput_bps": tput,
        "benchmark_avg_ms": bench_ms,
        "sender_rc": sender_rc,
        "receiver_rc": receiver_rc,
        "notes": notes.strip("; ").strip(),
    }


def load_rows(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def next_id(rows: list[dict]) -> int:
    if not rows:
        return 1
    return max(int(r["trial_id"]) for r in rows) + 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Karim: covert-channel trials under CPU interference"
    )
    parser.add_argument("--message", default="10101010")
    parser.add_argument(
        "--durations",
        default="100,200",
        help="Comma-separated bit durations (50,100,200)",
    )
    parser.add_argument("--levels", default="none,low,high")
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument(
        "--cpu",
        type=int,
        default=0,
        help="Pin sender+receiver with taskset -c N (-1 to disable)",
    )
    parser.add_argument("--lead-ms", type=int, default=5000)
    parser.add_argument(
        "--no-sender",
        action="store_true",
        help="Receiver-only control (R4 false-positive baseline)",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()

    if shutil.which("bash") is None:
        sys.exit("Requires bash (WSL/Linux).")
    if not re.fullmatch(r"[01]{1,1024}", args.message):
        sys.exit("Message must be 1..1024 binary digits.")

    durations = [int(x) for x in args.durations.split(",") if x.strip()]
    for d in durations:
        if d not in (50, 100, 200):
            sys.exit(f"Invalid duration {d}; use 50, 100, or 200")
    levels = [x.strip() for x in args.levels.split(",") if x.strip()]
    cpu = None if args.cpu < 0 else args.cpu

    ensure_channel_bins()
    RESULTS.mkdir(parents=True, exist_ok=True)
    log_dir = RESULTS / "channel_logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    if args.fresh and args.output.is_file():
        args.output.unlink()

    rows = load_rows(args.output)
    trial_id = next_id(rows)
    host = os.uname().nodename
    with_sender = not args.no_sender
    experiment = (
        "channel_under_interference"
        if with_sender
        else "no_sender_receiver_control"
    )

    for duration in durations:
        for level in levels:
            for t in range(1, args.trials + 1):
                tag = f"t{trial_id:03d}_d{duration}_{level}_{t}"
                print(
                    f"trial {trial_id}: duration={duration}ms level={level} "
                    f"sender={'yes' if with_sender else 'no'} ..."
                )
                result = run_one_trial(
                    message=args.message,
                    duration_ms=duration,
                    lead_ms=args.lead_ms,
                    interference_level=level,
                    affinity_cpu=cpu,
                    with_sender=with_sender,
                    log_dir=log_dir,
                    trial_tag=tag,
                )
                ber = result["ber"]
                ber_s = f"{ber:.6f}" if ber == ber else "nan"
                tput = result["throughput_bps"]
                tput_s = f"{tput:.4f}" if tput == tput else "nan"
                bench = result["benchmark_avg_ms"]
                bench_s = f"{bench:.6f}" if bench == bench else "nan"

                rows.append(
                    {
                        "trial_id": trial_id,
                        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "experiment": experiment,
                        "sent_bits": result["sent_bits"],
                        "decoded_bits": result["decoded_bits"],
                        "bit_duration_ms": result["bit_duration_ms"],
                        "interference_level": result["interference_level"],
                        "interference_workers": result["interference_workers"],
                        "affinity_cpu": result["affinity_cpu"],
                        "bit_errors": result["bit_errors"],
                        "ber": ber_s,
                        "throughput_bps": tput_s,
                        "benchmark_avg_ms": bench_s,
                        "sender_rc": result["sender_rc"],
                        "receiver_rc": result["receiver_rc"],
                        "host": host,
                        "notes": result["notes"],
                    }
                )
                print(
                    f"  decoded={result['decoded_bits'] or '(none)'} "
                    f"ber={ber_s} tput={tput_s} bench_ms={bench_s}"
                )
                trial_id += 1

    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CHANNEL_FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows -> {args.output}")


if __name__ == "__main__":
    main()