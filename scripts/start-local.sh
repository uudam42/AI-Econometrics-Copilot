#!/usr/bin/env bash
# AI Econometrics Copilot — Local Startup Script (macOS / Linux)
# Usage: bash scripts/start-local.sh

set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/logs"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- Dependency checks ---
check_python() {
    if command -v python3 &>/dev/null; then
        PY=python3
    elif command -v python &>/dev/null; then
        PY=python
    else
        error "Python 3 is not installed."
        echo "  Install Python 3.12+ from https://www.python.org/downloads/"
        exit 1
    fi
    PY_VER=$($PY --version 2>&1 | awk '{print $2}')
    PY_MAJOR=$($PY -c "import sys; print(sys.version_info.major)")
    PY_MINOR=$($PY -c "import sys; print(sys.version_info.minor)")
    if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
        error "Python $PY_VER found, but 3.10+ is required."
        exit 1
    fi
    info "Python: $PY_VER"
}

check_node() {
    if ! command -v node &>/dev/null; then
        error "Node.js is not installed."
        echo "  Install Node.js 18+ from https://nodejs.org/"
        exit 1
    fi
    NODE_VER=$(node --version | sed 's/v//')
    NODE_MAJOR=$(echo "$NODE_VER" | cut -d. -f1)
    if [ "$NODE_MAJOR" -lt 18 ]; then
        error "Node.js $NODE_VER found, but 18+ is required."
        exit 1
    fi
    info "Node.js: $NODE_VER"
}

# --- Setup ---
setup_backend() {
    cd "$BACKEND_DIR"
    if [ ! -d ".venv" ]; then
        info "Creating Python virtual environment..."
        $PY -m venv .venv
    fi
    source .venv/bin/activate

    if [ ! -f ".venv/.deps_installed" ] || [ requirements.txt -nt ".venv/.deps_installed" ]; then
        info "Installing backend dependencies..."
        pip install -q -r requirements.txt
        touch .venv/.deps_installed
    else
        info "Backend dependencies up to date."
    fi

    mkdir -p data/uploads data/artifacts
    cd "$ROOT_DIR"
}

setup_frontend() {
    cd "$FRONTEND_DIR"
    if [ ! -d "node_modules" ] || [ package.json -nt "node_modules/.package-lock.json" ] 2>/dev/null; then
        info "Installing frontend dependencies..."
        npm install --silent
    else
        info "Frontend dependencies up to date."
    fi
    cd "$ROOT_DIR"
}

# --- Launch ---
start_services() {
    mkdir -p "$LOG_DIR"

    info "Starting backend on http://localhost:8000 ..."
    cd "$BACKEND_DIR"
    source .venv/bin/activate
    uvicorn app.main:app --host 127.0.0.1 --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$LOG_DIR/backend.pid"
    cd "$ROOT_DIR"

    info "Starting frontend on http://localhost:3000 ..."
    cd "$FRONTEND_DIR"
    npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$LOG_DIR/frontend.pid"
    cd "$ROOT_DIR"

    # Wait for backend
    info "Waiting for backend to be ready..."
    for i in $(seq 1 30); do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            info "Backend is ready."
            break
        fi
        sleep 1
    done

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  AI Econometrics Copilot is running!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "  Frontend:  ${GREEN}http://localhost:3000${NC}"
    echo -e "  Backend:   ${GREEN}http://localhost:8000${NC}"
    echo -e "  API docs:  ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "  Logs:      $LOG_DIR/"
    echo -e "  Stop:      ${YELLOW}bash scripts/stop-local.sh${NC}"
    echo ""

    # Try to open browser
    if command -v open &>/dev/null; then
        open "http://localhost:3000" 2>/dev/null || true
    elif command -v xdg-open &>/dev/null; then
        xdg-open "http://localhost:3000" 2>/dev/null || true
    fi

    wait
}

# --- Main ---
echo ""
echo "AI Econometrics Copilot — Local Startup"
echo "========================================"
echo ""

check_python
check_node
setup_backend
setup_frontend
start_services
