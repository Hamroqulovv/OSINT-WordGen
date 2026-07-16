#!/usr/bin/env bash
# OSINT WordGen launcher (Linux / macOS)
# Creates a local virtualenv on first run, then forwards all arguments to main.py.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

PY="python3"
command -v "$PY" >/dev/null 2>&1 || PY="python"

if [ ! -d "$VENV_DIR" ]; then
  echo "[*] Creating virtual environment..."
  "$PY" -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  "$VENV_DIR/bin/python" -m pip install -r "$ROOT_DIR/requirements.txt"
fi

exec "$VENV_DIR/bin/python" "$ROOT_DIR/main.py" "$@"
