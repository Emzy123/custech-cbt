#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="${ROOT}/.local/pids"

stop_pidfile() {
  local name="$1" file="$2"
  if [[ -f "${file}" ]]; then
    local pid
    pid="$(cat "${file}")"
    if kill -0 "${pid}" 2>/dev/null; then
      kill "${pid}" 2>/dev/null || true
      printf 'Stopped %s (pid %s)\n' "${name}" "${pid}"
    fi
    rm -f "${file}"
  fi
}

stop_pidfile "frontend" "${PID_DIR}/frontend.pid"
stop_pidfile "backend" "${PID_DIR}/backend.pid"
stop_pidfile "redis" "${PID_DIR}/redis.pid"
stop_pidfile "mongodb" "${PID_DIR}/mongod.pid"

printf 'Manual test stack stopped.\n'
