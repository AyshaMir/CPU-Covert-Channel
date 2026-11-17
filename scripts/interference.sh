#!/usr/bin/env bash
# Configurable CPU load for covert-channel experiments (Karim).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${ROOT}/bin/interference"
PIDFILE="${ROOT}/results/.interference.pid"
LOGFILE="${ROOT}/results/.interference.log"

level_to_workers() {
    local level="$1"
    local n
    n="$(nproc 2>/dev/null || echo 4)"
    case "$level" in
        none) echo 0 ;;
        low) echo 1 ;;
        medium) echo $(( n / 2 > 0 ? n / 2 : 1 )) ;;
        high) echo "$n" ;;
        *)
            if [[ "$level" =~ ^[0-9]+$ ]] && [[ "$level" -ge 1 ]]; then
                echo "$level"
            else
                echo "Invalid level: $level (use none|low|medium|high|N)" >&2
                return 1
            fi
            ;;
    esac
}

is_running() {
    [[ -f "$PIDFILE" ]] || return 1
    local pid
    pid="$(cat "$PIDFILE")"
    kill -0 "$pid" 2>/dev/null
}

cmd_start() {
    local level="${1:-low}"
    local workers
    workers="$(level_to_workers "$level")" || exit 1

    if [[ "$workers" -eq 0 ]]; then
        echo "Level 'none' — nothing to start."
        return 0
    fi

    if is_running; then
        echo "Interference already running (pid $(cat "$PIDFILE"))." >&2
        exit 1
    fi

    if [[ ! -x "$BIN" ]]; then
        echo "Missing $BIN — run: ./scripts/build.sh" >&2
        exit 1
    fi

    mkdir -p "${ROOT}/results"
    nohup "$BIN" "$workers" >>"$LOGFILE" 2>&1 &
    echo $! >"$PIDFILE"
    echo "Started interference level=$level workers=$workers pid=$(cat "$PIDFILE")"
}

cmd_stop() {
    if ! is_running; then
        rm -f "$PIDFILE"
        echo "No interference process running."
        return 0
    fi
    local pid
    pid="$(cat "$PIDFILE")"
    kill -TERM "$pid" 2>/dev/null || true
    sleep 0.5
    kill -KILL "$pid" 2>/dev/null || true
    rm -f "$PIDFILE"
    echo "Stopped interference (was pid=$pid)."
}

cmd_status() {
    if is_running; then
        echo "running pid=$(cat "$PIDFILE")"
    else
        echo "stopped"
        rm -f "$PIDFILE"
    fi
}

usage() {
    echo "Usage: $0 {start [none|low|medium|high|N]|stop|status}"
    exit 1
}

case "${1:-}" in
    start) cmd_start "${2:-low}" ;;
    stop) cmd_stop ;;
    status) cmd_status ;;
    *) usage ;;
esac