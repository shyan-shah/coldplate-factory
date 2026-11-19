#!/usr/bin/env sh
# Launcher for macOS/Linux. Usage: ./run.sh [port]
cd "$(dirname "$0")"
PORT="${1:-8077}"
[ -d .venv ] || { python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt; }
[ -f .env ] || cp .env.example .env
.venv/bin/python -m uvicorn app.main:app --port "$PORT"
