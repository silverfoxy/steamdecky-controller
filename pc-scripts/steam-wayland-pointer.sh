#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
source_file="$script_dir/steam-wayland-pointer.c"
runtime_dir="${XDG_RUNTIME_DIR:-/tmp}"
binary="$runtime_dir/steam-wayland-pointer"
pid_file="$runtime_dir/steam-wayland-pointer.pid"
log_file="$runtime_dir/steam-wayland-pointer.log"

build() {
    if [ ! -x "$binary" ] || [ "$source_file" -nt "$binary" ]; then
        gcc -O2 -Wall -Wextra "$source_file" -o "$binary" -lX11
    fi
}

is_running() {
    [ -f "$pid_file" ] || return 1
    pid=$(sed -n '1p' "$pid_file")
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

case "${1:-start}" in
    start)
        build
        if is_running; then
            echo "Steam Wayland pointer bridge is already running (PID $pid)."
            exit 0
        fi
        nohup "$binary" >"$log_file" 2>&1 &
        pid=$!
        printf '%s\n' "$pid" >"$pid_file"
        sleep 0.1
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "Pointer bridge failed to start; see $log_file" >&2
            exit 1
        fi
        echo "Steam Wayland pointer bridge started (PID $pid)."
        ;;
    run)
        build
        exec "$binary"
        ;;
    stop)
        if is_running; then
            kill "$pid"
            swaymsg 'seat seat0 cursor release button1' >/dev/null 2>&1 || true
            swaymsg 'seat seat0 cursor release button2' >/dev/null 2>&1 || true
            swaymsg 'seat seat0 cursor release button3' >/dev/null 2>&1 || true
            echo "Steam Wayland pointer bridge stopped."
        else
            echo "Steam Wayland pointer bridge is not running."
        fi
        ;;
    status)
        if is_running; then
            echo "Steam Wayland pointer bridge is running (PID $pid)."
        else
            echo "Steam Wayland pointer bridge is not running."
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 {start|run|stop|status}" >&2
        exit 2
        ;;
esac
