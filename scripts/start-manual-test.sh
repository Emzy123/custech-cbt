#!/usr/bin/env bash
# Start MongoDB, Redis, backend, and frontend for manual testing.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL="${ROOT}/.local"
MONGO_DIR="${LOCAL}/mongodb"
REDIS_DIR="${LOCAL}/redis"
DATA_DIR="${LOCAL}/data"
PID_DIR="${LOCAL}/pids"
LOG_DIR="${LOCAL}/logs"
FNM_DIR="${LOCAL}/fnm"

export FNM_DIR
export PATH="${FNM_DIR}:${PATH}"
if [[ -x "${FNM_DIR}/fnm" ]]; then
  eval "$("${FNM_DIR}/fnm" env)"
fi

MONGO_PID="${PID_DIR}/mongod.pid"
REDIS_PID="${PID_DIR}/redis.pid"
BACKEND_PID="${PID_DIR}/backend.pid"
FRONTEND_PID="${PID_DIR}/frontend.pid"

log() { printf '==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

require_setup() {
  [[ -x "${MONGO_DIR}/bin/mongod" ]] || die "MongoDB not installed. Run: ./scripts/setup-manual-test.sh"
  [[ -x "${REDIS_DIR}/src/redis-server" ]] || die "Redis not built. Run: ./scripts/setup-manual-test.sh"
  [[ -d "${ROOT}/.venv" ]] || die "Python venv missing. Run: ./scripts/setup-manual-test.sh"
  [[ -d "${ROOT}/frontend/node_modules" ]] || die "Frontend deps missing. Run: ./scripts/setup-manual-test.sh"
}

wait_for_port() {
  local port="$1" name="$2" tries="${3:-30}"
  while (( tries-- > 0 )); do
    if (echo >/dev/tcp/127.0.0.1/"${port}") >/dev/null 2>&1; then
      log "${name} listening on port ${port}"
      return 0
    fi
    sleep 1
  done
  die "${name} did not start on port ${port}. Check ${LOG_DIR}"
}

start_mongo() {
  if [[ -f "${MONGO_PID}" ]] && kill -0 "$(cat "${MONGO_PID}")" 2>/dev/null; then
    log "MongoDB already running (pid $(cat "${MONGO_PID}"))"
    return
  fi
  log "Starting MongoDB"
  "${MONGO_DIR}/bin/mongod" \
    --dbpath "${DATA_DIR}/mongo" \
    --port 27017 \
    --bind_ip 127.0.0.1 \
    --logpath "${LOG_DIR}/mongod.log" \
    --fork \
    --pidfilepath "${MONGO_PID}"
  wait_for_port 27017 "MongoDB"
}

start_redis() {
  if [[ -f "${REDIS_PID}" ]] && kill -0 "$(cat "${REDIS_PID}")" 2>/dev/null; then
    log "Redis already running (pid $(cat "${REDIS_PID}"))"
    return
  fi
  log "Starting Redis"
  "${REDIS_DIR}/src/redis-server" \
    --port 6379 \
    --bind 127.0.0.1 \
    --dir "${DATA_DIR}/redis" \
    --daemonize yes \
    --pidfile "${REDIS_PID}" \
    --logfile "${LOG_DIR}/redis.log"
  wait_for_port 6379 "Redis"
}

seed_if_needed() {
  # shellcheck disable=SC1091
  source "${ROOT}/.venv/bin/activate"
  if [[ ! -f "${LOCAL}/.seeded" ]]; then
    log "Seeding database (first run)"
    python "${ROOT}/seed_admin.py"
    python "${ROOT}/seed_users.py"
    python "${ROOT}/seed_officers.py"
    touch "${LOCAL}/.seeded"
  else
    log "Database already seeded (delete .local/.seeded to re-seed)"
  fi
}

start_backend() {
  if [[ -f "${BACKEND_PID}" ]] && kill -0 "$(cat "${BACKEND_PID}")" 2>/dev/null; then
    log "Backend already running (pid $(cat "${BACKEND_PID}"))"
    return
  fi
  log "Starting backend on http://localhost:8000"
  # shellcheck disable=SC1091
  source "${ROOT}/.venv/bin/activate"
  nohup python "${ROOT}/run_backend.py" >>"${LOG_DIR}/backend.log" 2>&1 &
  echo $! >"${BACKEND_PID}"
  wait_for_port 8000 "Backend"
}

start_frontend() {
  if [[ -f "${FRONTEND_PID}" ]] && kill -0 "$(cat "${FRONTEND_PID}")" 2>/dev/null; then
    log "Frontend already running (pid $(cat "${FRONTEND_PID}"))"
    return
  fi
  log "Starting frontend on http://localhost:3000"
  cd "${ROOT}/frontend"
  export BROWSER=none
  export DANGEROUSLY_DISABLE_HOST_CHECK=true
  nohup npm start >>"${LOG_DIR}/frontend.log" 2>&1 &
  echo $! >"${FRONTEND_PID}"
  cd "${ROOT}"
  wait_for_port 3000 "Frontend" 120
}

print_summary() {
  cat <<EOF

Manual testing environment is up.

  UI:          http://localhost:3000
  API:         http://localhost:8000
  API docs:    http://localhost:8000/docs

Test accounts (passwords are dev-only):

  Role            Username       Password
  --------------  -------------  ---------------
  Super Admin     admin          Admin123!
  Lecturer        lecturer       Lecturer123!
  Student         student        Student123!
  Exam Officer    examofficer    ExamOfficer123!
  Invigilator     invigilator    Invigilator123!

Logs: ${LOG_DIR}/
Stop: ./scripts/stop-manual-test.sh

EOF
}

main() {
  cd "${ROOT}"
  mkdir -p "${PID_DIR}" "${LOG_DIR}"
  require_setup
  start_mongo
  start_redis
  seed_if_needed
  start_backend
  start_frontend
  print_summary
}

main "$@"
