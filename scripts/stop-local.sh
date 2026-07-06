#!/usr/bin/env bash
# Stop locally running AI Econometrics Copilot services

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"

stop_pid() {
    local name=$1
    local pidfile="$LOG_DIR/$name.pid"
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            echo "Stopped $name (PID $pid)"
        else
            echo "$name is not running (stale PID $pid)"
        fi
        rm -f "$pidfile"
    else
        echo "No PID file for $name"
    fi
}

stop_pid "backend"
stop_pid "frontend"

# Also kill any remaining processes on the ports
for port in 8000 3000; do
    pid=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$pid" ]; then
        kill $pid 2>/dev/null && echo "Killed process on port $port (PID $pid)"
    fi
done

echo ""
echo "All services stopped."
