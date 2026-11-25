#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== Starting Opportunity Agent ==="

# 1. Check .env
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# 2. Check virtual environment
PYTHON_EXE="$PROJECT_DIR/.venv/bin/python"
UVICORN_EXE="$PROJECT_DIR/.venv/bin/uvicorn"
ALEMBIC_EXE="$PROJECT_DIR/.venv/bin/alembic"

if [ ! -f "$PYTHON_EXE" ]; then
    echo "Virtual environment not found. Creating..."
    if command -v uv >/dev/null 2>&1; then
        uv venv --python 3.11
        uv pip install -e ".[dev]"
    else
        python3 -m venv .venv
        "$PROJECT_DIR/.venv/bin/pip" install -e ".[dev]"
    fi
fi

# 3. Ensure data directory exists
mkdir -p data

# 4. Apply database migrations
echo "Applying database migrations..."
"$ALEMBIC_EXE" upgrade head

# 5. Check frontend build
if [ -f "frontend/package.json" ] && [ ! -d "frontend/dist" ]; then
    echo "Building frontend..."
    cd frontend
    if command -v npm >/dev/null 2>&1; then
        npm install
        npm run build
    fi
    cd "$PROJECT_DIR"
fi

# 6. Start server
echo "Starting FastAPI server on http://127.0.0.1:8000 ..."
"$UVICORN_EXE" app.main:app --host 127.0.0.1 --port 8000 --reload
