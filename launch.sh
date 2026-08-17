#!/usr/bin/env bash
# GenAI Systems Lab — Linux/macOS launcher
# First-time setup: installs uv, creates .venv, installs all dependencies,
# then starts the FastAPI backend and Next.js frontend.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"
DATA_DIR="$SCRIPT_DIR/.data"
FRONTEND_DIR="$SCRIPT_DIR/portfolio"
BACKEND_PORT=8514
FRONTEND_PORT=8513
BACKEND_PID_FILE="$DATA_DIR/backend.pid"
FRONTEND_PID_FILE="$DATA_DIR/frontend.pid"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[GenAI Systems Lab]${NC} $*"; }
warn()    { echo -e "${YELLOW}[GenAI Systems Lab]${NC} $*"; }
error()   { echo -e "${RED}[GenAI Systems Lab]${NC} $*" >&2; }

# ── uv ──────────────────────────────────────────────────────────────────────
install_uv() {
  if command -v uv &>/dev/null; then return; fi
  info "uv not found — installing..."
  if command -v pip &>/dev/null; then
    pip install --quiet uv && return
  fi
  if command -v curl &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Reload PATH for the current shell
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
    return
  fi
  error "Cannot install uv: neither pip nor curl is available."
  error "Install uv manually from https://docs.astral.sh/uv/getting-started/installation/ and re-run."
  exit 1
}

# ── Node.js ──────────────────────────────────────────────────────────────────
check_node() {
  if command -v node &>/dev/null && command -v npm &>/dev/null; then return; fi
  warn "Node.js / npm not found. Installing the frontend will fail."
  warn "Install Node.js LTS from https://nodejs.org and re-run."
  warn "Backend-only mode will still work at http://localhost:$BACKEND_PORT"
}

# ── Python venv ──────────────────────────────────────────────────────────────
setup_venv() {
  if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating .venv in project root with uv..."
    uv venv "$VENV_DIR"
  fi
  # Install / sync dependencies into .venv
  info "Syncing Python dependencies with uv..."
  uv sync --all-extras
}

# ── .data directory & encryption key ────────────────────────────────────────
setup_data() {
  mkdir -p "$DATA_DIR"
  if [[ ! -f "$DATA_DIR/launcher.env" ]]; then
    info "Generating persistent Fernet encryption key..."
    python3 -c "
from cryptography.fernet import Fernet
key = Fernet.generate_key().decode()
with open('$DATA_DIR/launcher.env', 'w') as f:
    f.write(f'GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY={key}\n')
" 2>/dev/null || {
      # Fallback if cryptography not yet installed
      KEY=$(python3 -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())" 2>/dev/null || openssl rand -base64 32 | tr '+/' '-_' | tr -d '=\n')
      echo "GENAI_SYSTEMS_LAB_BYOK_ENCRYPTION_KEY=$KEY" > "$DATA_DIR/launcher.env"
    }
  fi
}

# ── .env file ────────────────────────────────────────────────────────────────
setup_env() {
  if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
    info "Creating .env from .env.example..."
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    warn "Edit .env to set GENAI_SYSTEMS_LAB_JWT_SECRET for production use."
  fi
  # Append/export the launcher Fernet key into the current env
  if [[ -f "$DATA_DIR/launcher.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$DATA_DIR/launcher.env"
    set +a
  fi
}

# ── Port availability ────────────────────────────────────────────────────────
check_port() {
  local port=$1 name=$2
  if lsof -i "TCP:$port" -sTCP:LISTEN &>/dev/null 2>&1; then
    warn "Port $port is already in use ($name)."
    warn "The running process may already be GenAI Systems Lab — check http://localhost:$port"
    return 1
  fi
  return 0
}

# ── Backend ──────────────────────────────────────────────────────────────────
start_backend() {
  if ! check_port "$BACKEND_PORT" "FastAPI backend"; then
    info "Skipping backend start — already running on port $BACKEND_PORT"
    return
  fi
  info "Starting FastAPI backend on port $BACKEND_PORT..."
  nohup uv run uvicorn shared.api.app:app \
    --host 0.0.0.0 --port "$BACKEND_PORT" \
    > "$DATA_DIR/backend.log" 2>&1 &
  echo $! > "$BACKEND_PID_FILE"
  info "Backend log: $DATA_DIR/backend.log  (PID $(cat "$BACKEND_PID_FILE"))"
}

wait_for_backend() {
  info "Waiting for backend to become healthy..."
  local deadline=$((SECONDS + 60))
  while [[ $SECONDS -lt $deadline ]]; do
    if curl -sf "http://127.0.0.1:$BACKEND_PORT/health" &>/dev/null; then
      info "Backend is healthy."
      return
    fi
    sleep 2
  done
  error "Backend did not become healthy within 60 s."
  error "Check logs: $DATA_DIR/backend.log"
  exit 1
}

# ── Frontend ─────────────────────────────────────────────────────────────────
start_frontend() {
  if ! command -v node &>/dev/null; then
    warn "Skipping frontend — Node.js not installed."
    return
  fi
  if ! check_port "$FRONTEND_PORT" "Next.js frontend"; then
    info "Skipping frontend start — already running on port $FRONTEND_PORT"
    return
  fi
  info "Installing frontend dependencies..."
  (cd "$FRONTEND_DIR" && npm install --no-audit --no-fund --silent)
  info "Starting Next.js frontend on port $FRONTEND_PORT..."
  nohup bash -c "cd \"$FRONTEND_DIR\" && npm run dev" \
    > "$DATA_DIR/frontend.log" 2>&1 &
  echo $! > "$FRONTEND_PID_FILE"
  info "Frontend log: $DATA_DIR/frontend.log  (PID $(cat "$FRONTEND_PID_FILE"))"
}

wait_for_frontend() {
  if ! command -v node &>/dev/null; then return; fi
  info "Waiting for frontend to become ready..."
  local deadline=$((SECONDS + 120))
  while [[ $SECONDS -lt $deadline ]]; do
    if curl -sf "http://127.0.0.1:$FRONTEND_PORT/" &>/dev/null; then
      info "Frontend is ready."
      return
    fi
    sleep 2
  done
  warn "Frontend did not respond within 120 s."
  warn "Check logs: $DATA_DIR/frontend.log"
}

open_browser() {
  local url="http://localhost:$FRONTEND_PORT"
  if command -v node &>/dev/null; then
    info "Opening $url ..."
    if command -v xdg-open &>/dev/null; then
      xdg-open "$url" &>/dev/null &
    elif command -v open &>/dev/null; then
      open "$url"
    else
      info "Open your browser at $url"
    fi
  else
    info "API ready at http://localhost:$BACKEND_PORT"
    info "Frontend skipped — install Node.js and re-run to get the UI."
  fi
}

# ── Cleanup on Ctrl+C ────────────────────────────────────────────────────────
cleanup() {
  echo ""
  warn "Stopping services..."
  if [[ -f "$BACKEND_PID_FILE" ]]; then
    kill "$(cat "$BACKEND_PID_FILE")" 2>/dev/null || true
    rm -f "$BACKEND_PID_FILE"
  fi
  if [[ -f "$FRONTEND_PID_FILE" ]]; then
    kill "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null || true
    rm -f "$FRONTEND_PID_FILE"
  fi
  info "Stopped. Goodbye."
  exit 0
}
trap cleanup INT TERM

# ── Main ──────────────────────────────────────────────────────────────────────
echo ""
info "GenAI Systems Lab Launcher"
echo ""

install_uv
check_node
setup_venv
setup_data
setup_env
start_backend
wait_for_backend
start_frontend
wait_for_frontend
open_browser

echo ""
info "Ready."
info "  Backend:  http://localhost:$BACKEND_PORT"
info "  API docs: http://localhost:$BACKEND_PORT/docs"
if command -v node &>/dev/null; then
  info "  Frontend: http://localhost:$FRONTEND_PORT"
fi
echo ""
info "Press Ctrl+C to stop all services."
echo ""

# Keep the script alive so Ctrl+C triggers cleanup
wait
