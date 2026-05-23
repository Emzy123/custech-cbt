#!/usr/bin/env bash
# Bootstrap MongoDB, Redis, Python venv, Node, and seed data for local manual testing.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL="${ROOT}/.local"
MONGO_DIR="${LOCAL}/mongodb"
REDIS_DIR="${LOCAL}/redis"
DATA_DIR="${LOCAL}/data"
PID_DIR="${LOCAL}/pids"
LOG_DIR="${LOCAL}/logs"
FNM_DIR="${LOCAL}/fnm"
MONGO_VERSION="7.0.18"
REDIS_VERSION="7.2.4"
NODE_VERSION="20"

export FNM_DIR
export PATH="${FNM_DIR}:${PATH}"

fnm_env() {
  eval "$("${FNM_DIR}/fnm" env)"
}

log() { printf '\n==> %s\n' "$*"; }

ensure_env() {
  if [[ ! -f "${ROOT}/.env" ]]; then
    log "Creating .env from .env.example"
    cp "${ROOT}/.env.example" "${ROOT}/.env"
    cat >> "${ROOT}/.env" <<'EOF'

# Added by scripts/setup-manual-test.sh
SEED_ADMIN_PASSWORD=Admin123!
JWT_SECRET=dev-jwt-secret-key-change-in-production
SECRET_KEY=dev-secret-key-for-session-management
RANDOMISATION_SECRET=dev-randomisation-secret-change-me
BIOMETRIC_ENCRYPTION_KEY=dev-biometric-key-32-bytes-long!!
EOF
  fi
}

ensure_dirs() {
  mkdir -p "${DATA_DIR}/mongo" "${DATA_DIR}/redis" "${PID_DIR}" "${LOG_DIR}"
}

install_mongodb() {
  if [[ -x "${MONGO_DIR}/bin/mongod" ]]; then
    log "MongoDB already installed in .local/mongodb"
    return
  fi
  log "Downloading MongoDB ${MONGO_VERSION}"
  mkdir -p "${LOCAL}/downloads"
  local tgz="${LOCAL}/downloads/mongodb-linux-x86_64-ubuntu2204-${MONGO_VERSION}.tgz"
  if [[ ! -f "${tgz}" ]]; then
    curl -fsSL \
      "https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu2204-${MONGO_VERSION}.tgz" \
      -o "${tgz}"
  fi
  rm -rf "${MONGO_DIR}"
  tar -xzf "${tgz}" -C "${LOCAL}"
  mv "${LOCAL}/mongodb-linux-x86_64-ubuntu2204-${MONGO_VERSION}" "${MONGO_DIR}"
  log "MongoDB installed"
}

install_redis() {
  if [[ -x "${REDIS_DIR}/src/redis-server" ]]; then
    log "Redis already built in .local/redis"
    return
  fi
  log "Building Redis ${REDIS_VERSION} (requires gcc/make)"
  mkdir -p "${LOCAL}/downloads"
  local tgz="${LOCAL}/downloads/redis-${REDIS_VERSION}.tar.gz"
  if [[ ! -f "${tgz}" ]]; then
    curl -fsSL "https://download.redis.io/releases/redis-${REDIS_VERSION}.tar.gz" -o "${tgz}"
  fi
  rm -rf "${REDIS_DIR}"
  mkdir -p "${REDIS_DIR}"
  tar -xzf "${tgz}" -C "${LOCAL}/downloads"
  cp -a "${LOCAL}/downloads/redis-${REDIS_VERSION}/." "${REDIS_DIR}/"
  make -C "${REDIS_DIR}" -j"$(nproc 2>/dev/null || echo 2)" >/dev/null
  log "Redis built"
}

install_node() {
  if command -v npm >/dev/null 2>&1 && [[ "$(node -v 2>/dev/null || true)" == v${NODE_VERSION}* ]]; then
    log "Node $(node -v) and npm already available"
    return
  fi
  if [[ ! -x "${FNM_DIR}/fnm" ]]; then
    log "Installing fnm (Node version manager)"
    mkdir -p "${FNM_DIR}"
    curl -fsSL https://fnm.vercel.app/install | bash -s -- --install-dir "${FNM_DIR}" --skip-shell
  fi
  fnm_env
  "${FNM_DIR}/fnm" install "${NODE_VERSION}"
  "${FNM_DIR}/fnm" use "${NODE_VERSION}"
  fnm_env
  log "Node $(node -v) ready via fnm"
}

install_uv() {
  if command -v uv >/dev/null 2>&1; then
    return
  fi
  if [[ -x "${LOCAL}/uv/uv" ]]; then
    export PATH="${LOCAL}/uv:${PATH}"
    return
  fi
  log "Installing uv (Python package manager)"
  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="${LOCAL}/uv" sh
  export PATH="${LOCAL}/uv:${PATH}"
}

install_python() {
  install_uv
  if [[ ! -x "${ROOT}/.venv/bin/python" ]]; then
    log "Creating Python virtual environment"
    if python3 -m venv "${ROOT}/.venv" 2>/dev/null; then
      :
    else
      rm -rf "${ROOT}/.venv"
      uv venv "${ROOT}/.venv"
    fi
  fi
  if command -v uv >/dev/null 2>&1; then
    uv pip install -r "${ROOT}/requirements.txt"
  else
    # shellcheck disable=SC1091
    source "${ROOT}/.venv/bin/activate"
    pip install -q --upgrade pip
    pip install -q -r "${ROOT}/requirements.txt"
  fi
  log "Python dependencies installed"
}

install_frontend() {
  fnm_env
  log "Installing frontend npm packages"
  cd "${ROOT}/frontend"
  npm install --legacy-peer-deps
  cd "${ROOT}"
}

main() {
  cd "${ROOT}"
  ensure_env
  ensure_dirs
  install_mongodb
  install_redis
  install_node
  install_python
  install_frontend
  log "Setup complete. Run: ./scripts/start-manual-test.sh (seeds users on first start)"
}

main "$@"
