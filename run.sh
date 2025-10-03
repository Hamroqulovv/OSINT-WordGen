#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

# Create and activate venv only once
if [ ! -d "$VENV_DIR" ]; then
  echo "[*] Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
  source "$VENV_DIR/bin/activate"
  pip install --upgrade pip
  pip install -r "$ROOT_DIR/requirements.txt"
else
  # activate existing venv
  source "$VENV_DIR/bin/activate"
fi

# run main with all args forwarded
python3 "$ROOT_DIR/main.py" "$@"
